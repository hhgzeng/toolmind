import json
from typing import List, Optional

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    BaseMessage,
    AIMessageChunk,
)
from langchain_core.tools.base import ToolException
from langchain_core.utils.function_calling import convert_to_openai_tool

from toolmind.api.services.mcp_server import MCPService
from toolmind.api.services.mcp_user_config import MCPUserConfigService
from toolmind.api.services.usage_stats import UsageStatsService
from toolmind.api.services.workspace_session import WorkSpaceSessionService
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.database.models.workspace_session import (
    WorkSpaceSessionCreate,
    WorkSpaceSessionContext,
)
from toolmind.schema.workspace import WorkSpaceAgents
from toolmind.schema.usage_stats import UsageStatsAgentType
from toolmind.core.agents.mcp_agent import MCPConfig
from toolmind.services.web_search.action import tavily_search as web_search
from toolmind.settings import app_settings
from toolmind.core.models.manager import ModelManager
from toolmind.utils.convert import mcp_tool_to_args_schema, convert_mcp_config
from toolmind.utils.date_utils import get_beijing_time
from toolmind.services.mcp.manager import MCPManager
from toolmind.prompts.mind import (
    GenerateTitlePrompt,
    GenerateTaskPrompt,
    FixJsonPrompt,
    ToolCallPrompt,
    SystemMessagePrompt,
    FinalSynthesisPrompt,
    EvaluateResultPrompt,
)
from toolmind.schema.mind import MindTask, MindTaskStep


class MindAgent:

    def __init__(self, user_id: str):
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_tools = []
        self.tool_mcp_server_dict = {}

        self.user_id = user_id

    async def get_conversation_model(self):
        return await ModelManager.get_conversation_model(user_id=self.user_id)

    async def get_tool_call_model(self):
        return await ModelManager.get_mind_intent_model(user_id=self.user_id)

    async def get_reasoning_model(self):
        return await ModelManager.get_reasoning_model(user_id=self.user_id)

    async def _generate_tasks(self, mind_task_prompt):
        model = await self.get_conversation_model()
        conversation_json_model = model.bind(response_format={"type": "json_object"})

        response = await conversation_json_model.ainvoke(
            input=mind_task_prompt, config={"callbacks": [usage_metadata_callback]}
        )

        try:
            content = json.loads(response.content)
            return content
        except Exception as err:
            fix_message = FixJsonPrompt.format(
                json_content=response.content, json_error=str(err)
            )
            fix_response = await conversation_json_model.ainvoke(
                input=fix_message, config={"callbacks": [usage_metadata_callback]}
            )
            try:
                fix_content = json.loads(fix_response.content)
                return fix_content
            except Exception as fix_err:
                raise ValueError(fix_err)

    async def _generate_title(self, query):
        title_prompt = GenerateTitlePrompt.format(query=query)
        model = await self.get_conversation_model()
        response = await model.ainvoke(
            input=title_prompt, config={"callbacks": [usage_metadata_callback]}
        )
        return response.content

    async def _add_workspace_session(self, query, contexts: WorkSpaceSessionContext):
        title = await self._generate_title(query)
        await WorkSpaceSessionService.create_workspace_session(
            WorkSpaceSessionCreate(
                title=title,
                user_id=self.user_id,
                contexts=[contexts.model_dump()],
                agent=WorkSpaceAgents.MindAgent.value,
            )
        )

    async def _parse_function_call_response(self, message: AIMessage):
        tool_messages = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")
                tool_call_id = tool_call.get("id")

                content = await self._process_tools_result(tool_name, tool_args)
                tool_messages.append(
                    ToolMessage(
                        content=content, name=tool_name, tool_call_id=tool_call_id
                    )
                )

        return tool_messages

    async def generate_tasks(self, mind_task: MindTask):
        tools = await self._obtain_mind_tools(
            mind_task.mcp_servers, mind_task.web_search
        )
        tools_str = json.dumps(tools, ensure_ascii=False, indent=2)
        attachments_str = json.dumps(
            [attachment.model_dump() for attachment in mind_task.attachments],
            ensure_ascii=False,
            indent=2,
        )

        mind_task_prompt = GenerateTaskPrompt.format(
            tools_str=tools_str,
            query=mind_task.query,
            current_time=get_beijing_time(),
            attachments_str=attachments_str,
        )

        response_task = await self._generate_tasks(mind_task_prompt)
        return response_task

    async def _evaluate_result(
        self,
        query: str,
        answer: str,
        mcp_servers: List[str],
        enable_web_search: bool = True,
    ) -> dict:
        """
        使用推理模型（ReasoningModel）对生成结果进行多轮工具调用评估。
        ReasoningModel 在序列化时会正确携带 reasoning_content，
        因此支持 DeepSeek Reasoner 等推理模型的多轮对话。
        """
        import re

        eval_prompt = EvaluateResultPrompt.format(query=query, answer=answer)
        messages: List[BaseMessage] = [
            SystemMessage(content="你是一个专业的结果评判助手。"),
            HumanMessage(content=eval_prompt),
        ]

        tools = await self._obtain_mind_tools(mcp_servers, enable_web_search)
        model = await self.get_reasoning_model()
        eval_model = model.bind_tools(tools) if len(tools) else model

        content = ""
        try:
            while True:
                response = await eval_model.ainvoke(
                    input=messages, config={"callbacks": [usage_metadata_callback]}
                )
                messages.append(response)

                if response.tool_calls:
                    tool_messages = await self._parse_function_call_response(response)
                    messages.extend(tool_messages)
                else:
                    break

            content = response.content.strip()
            print(f"[DEBUG _evaluate_result] Raw LLM response: {content}")

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            json_str = json_match.group(0) if json_match else content

            parsed_json = json.loads(json_str)
            print(f"[DEBUG _evaluate_result] Parsed JSON data: {parsed_json}")
            return parsed_json
        except Exception as err:
            import openai

            print(f"[DEBUG _evaluate_result] Exception occurred first time: {err}")
            if (
                isinstance(err, openai.RateLimitError)
                or "insufficient_quota" in str(err)
                or "429" in str(err)
            ):
                return {
                    "score": 80,
                    "reasoning": "评判模型触发限流或余额不足 (RateLimitError/Insufficient Quota)，默认算作通过。",
                }

            try:
                # 尝试修复一般的 JSON 格式错误
                json_content_to_fix = content or locals().get("content", "")
                fix_message = FixJsonPrompt.format(
                    json_content=json_content_to_fix, json_error=str(err)
                )
                fix_model = await self.get_conversation_model()
                fix_response = await fix_model.ainvoke(
                    input=fix_message, config={"callbacks": [usage_metadata_callback]}
                )
                fix_content = fix_response.content.strip()

                json_match = re.search(r"\{.*\}", fix_content, re.DOTALL)
                if json_match:
                    fix_content = json_match.group(0)

                return json.loads(fix_content)
            except Exception as e:
                return {
                    "score": 100,
                    "reasoning": f"评判执行异常: {str(e)}，默认放行。",
                }

    async def submit_mind_task(self, mind_task: MindTask):
        # 首次收到用户问题时，先创建一个临时工作区会话，标题固定为「新对话」
        workspace_session = await WorkSpaceSessionService.create_workspace_session(
            WorkSpaceSessionCreate(
                title="新对话",
                user_id=self.user_id,
                contexts=[],
                agent=WorkSpaceAgents.MindAgent.value,
            )
        )
        # 将新会话的基础信息通过 SSE 推送给前端，便于侧边栏立即展示
        yield {
            "event": "session_started",
            "data": {
                "session_id": workspace_session.session_id,
                "title": workspace_session.title,
                "agent": workspace_session.agent,
                "create_time": workspace_session.create_time.isoformat()
                if workspace_session.create_time
                else None,
            },
        }

        loop_count = 0
        max_loop = 3

        while loop_count < max_loop:
            loop_count += 1
            if loop_count > 1:
                yield {
                    "event": "step_result",
                    "data": {
                        "message": "正在重新规划任务并重头执行...",
                        "title": f"第 {loop_count} 次重跑",
                    },
                }

            task = await self.generate_tasks(mind_task)

            # 将规划结果转换为步骤对象，保持原始顺序（严格串行链路）
            tasks_graph: dict[str, MindTaskStep] = {}
            tasks_show = []
            raw_steps = task.get("steps", [])
            steps: List[MindTaskStep] = []
            for raw_step in raw_steps:
                task_step = MindTaskStep(**raw_step)
                steps.append(task_step)
                tasks_graph[task_step.step_id] = task_step

            # 构建用于前端展示的简化任务图结构（用户问题 -> step_1 -> step_2 -> ...）
            for step_info in steps:
                if not step_info.input:
                    # 没有前置输入，默认从用户问题开始
                    tasks_show.append({"start": "用户问题", "end": step_info.title})
                else:
                    for input_step in step_info.input:
                        if input_step in tasks_graph:
                            tasks_show.append(
                                {
                                    "start": tasks_graph[input_step].title,
                                    "end": step_info.title,
                                }
                            )
                        else:
                            tasks_show.append(
                                {"start": "用户问题", "end": step_info.title}
                            )
            yield {"event": "generate_tasks", "data": {"graph": tasks_show}}

            tools = await self._obtain_mind_tools(
                mind_task.mcp_servers, mind_task.web_search
            )
            model = await self.get_tool_call_model()
            tool_call_model = model.bind_tools(tools) if len(tools) else model

            context_task = []
            # 逐个步骤串行执行，每个步骤内部允许多轮工具调用，最终产生该步骤的总结结果
            for step_info in steps:
                # 构建当前步骤的上下文（仅包含直接前置步骤，严格串行链路下通常只有一个）
                step_context = []
                for input_step in step_info.input:
                    if input_step in tasks_graph:
                        step_context.append(tasks_graph[input_step].model_dump())

                # 执行当前步骤：模型可以自行决定是否调用工具，多轮调用后输出步骤总结
                step_prompt = ToolCallPrompt.format(
                    step_info=step_info.model_dump(),
                    step_context=json.dumps(step_context, ensure_ascii=False, indent=2),
                    user_query=mind_task.query,
                    attachments_json=json.dumps(
                        [a.model_dump() for a in mind_task.attachments],
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
                step_messages: List[BaseMessage] = [
                    SystemMessage(content=step_prompt),
                    HumanMessage(content=mind_task.query),
                ]

                step_summary = ""
                while True:
                    response = await tool_call_model.ainvoke(
                        input=step_messages,
                        config={"callbacks": [usage_metadata_callback]},
                    )
                    step_messages.append(response)

                    if response.tool_calls:
                        # 如果还有工具调用请求，先执行工具并将结果追加到对话中，然后继续循环
                        tool_messages = await self._parse_function_call_response(
                            response
                        )
                        step_messages.extend(tool_messages)
                    else:
                        # 没有新的工具调用时，将最后一次回复视为该子任务的总结结果
                        step_summary = response.content or ""
                        break

                step_info.result = step_summary
                context_task.append(step_info.model_dump())

                # 向前端推送当前步骤的执行结果（用于 To-dos 列表展示）
                yield {
                    "event": "step_result",
                    "data": {
                        "message": step_info.result or " ",
                        "title": step_info.title,
                    },
                }

            # 所有子任务执行完成后，使用对话模型基于所有步骤结果生成最终汇总答案
            final_steps_payload = [
                {
                    "step_id": step.step_id,
                    "title": step.title,
                    "target": step.target,
                    "result": step.result,
                }
                for step in steps
            ]

            synthesis_prompt = FinalSynthesisPrompt.format(
                query=mind_task.query,
                steps_json=json.dumps(
                    final_steps_payload, ensure_ascii=False, indent=2
                ),
            )

            final_response = ""
            conversation_model = await self.get_conversation_model()
            async for chunk in conversation_model.astream(
                [HumanMessage(content=synthesis_prompt)],
                config={"callbacks": [usage_metadata_callback]},
            ):
                final_response += chunk.content
                yield {
                    "event": "task_result",
                    "data": {"message": chunk.content},
                }

            # Evaluation check
            print(f"[{get_beijing_time()}] [MindAgent] Start _evaluate_result...")
            yield {"event": "evaluating_result", "data": {}}
            eval_res = await self._evaluate_result(
                query=mind_task.query,
                answer=final_response,
                mcp_servers=mind_task.mcp_servers,
                enable_web_search=mind_task.web_search,
            )
            score = eval_res.get("score", 100)
            reasoning = eval_res.get("reasoning", "")
            print(
                f"[{get_beijing_time()}] [MindAgent] Evaluated result -> Score: {score}, Reasoning: {reasoning}"
            )

            if score >= 80 or loop_count == max_loop:
                # 自我反馈通过（或达到最大重试次数时），在答案末尾追加通过信息，并持久化当前轮次完整结果
                pass_msg = (
                    f"\n\n\n> **✅ 自我反馈通过** (匹配度: {score}/100)\n"
                    f"> **理由**: {reasoning}\n\n---\n\n"
                )
                yield {"event": "task_result", "data": {"message": pass_msg}}
                final_response_with_feedback = final_response + pass_msg

                # 追加本次任务的上下文信息（task、task_graph、answer）
                await WorkSpaceSessionService.update_workspace_session_contexts(
                    workspace_session.session_id,
                    WorkSpaceSessionContext(
                        query=mind_task.query,
                        task=context_task,
                        task_graph=tasks_show,
                        answer=final_response_with_feedback,
                    ).model_dump(),
                )

                # 使用对话模型流式生成会话标题，并将最新标题实时推送给前端
                title_prompt = GenerateTitlePrompt.format(query=mind_task.query)
                conversation_model_for_title = await self.get_conversation_model()
                streamed_title = ""
                async for title_chunk in conversation_model_for_title.astream(
                    input=title_prompt,
                    config={"callbacks": [usage_metadata_callback]},
                ):
                    chunk_content = getattr(title_chunk, "content", "") or ""
                    if not chunk_content:
                        continue
                    streamed_title += chunk_content
                    # 将当前累计标题流式发送给前端，用于侧边栏实时展示命名过程
                    yield {
                        "event": "session_title_chunk",
                        "data": {
                            "session_id": workspace_session.session_id,
                            "title": streamed_title,
                        },
                    }

                final_title = streamed_title.strip() or "新对话"

                # 持久化最终标题
                await WorkSpaceSessionService.update_workspace_session(
                    workspace_session.session_id,
                    self.user_id,
                    title=final_title,
                    is_pinned=None,
                )

                # 再发送一次最终标题，方便前端在需要时做一次性刷新
                yield {
                    "event": "session_updated",
                    "data": {
                        "session_id": workspace_session.session_id,
                        "title": final_title,
                    },
                }
                break
            else:
                # 自我反馈未通过时，同样将该轮的完整答案（含失败原因）持久化为一次独立结果
                retry_msg = (
                    f"\n\n\n> **⚠️ 自我反馈未通过** (匹配度: {score}/100)\n"
                    f"> **理由**: {reasoning}\n"
                    f"> \n> __系统正在进行第 {loop_count + 1} 次重跑尝试...__\n\n---\n\n"
                )
                yield {"event": "task_result", "data": {"message": retry_msg}}
                final_response_with_feedback = final_response + retry_msg

                await WorkSpaceSessionService.update_workspace_session_contexts(
                    workspace_session.session_id,
                    WorkSpaceSessionContext(
                        query=mind_task.query,
                        task=context_task,
                        task_graph=tasks_show,
                        answer=final_response_with_feedback,
                    ).model_dump(),
                )

    async def _process_tools_result(self, tool_name, tool_args):
        def find_mcp_tool(tool_name):
            """Find MCP tool by name"""
            for tool in self.mcp_tools:
                if tool.name == tool_name:
                    return tool
            return None

        if tool := find_mcp_tool(tool_name):
            server_id = self.tool_mcp_server_dict.get(tool_name)
            if server_id:
                mcp_config = await MCPUserConfigService.get_mcp_user_config(
                    self.user_id, server_id
                )
                tool_args.update(mcp_config)
            try:
                text_content, no_text_content = await tool.coroutine(**tool_args)
            except ToolException as e:
                text_content = f"[工具执行失败] {tool_name}: {e}"
            except Exception as e:
                text_content = f"[工具执行失败] {tool_name}: {type(e).__name__} - {e}"
        else:
            if tool_name == "web_search":
                from toolmind.services.web_search.action import _tavily_search
                from toolmind.database.dao.web_search_config import WebSearchConfigDao
                
                user_config = await WebSearchConfigDao.get_config_by_user_id(self.user_id)
                api_key = user_config.api_key if user_config else None
                
                text_content = _tavily_search(**tool_args, api_key=api_key)
            else:
                text_content = f"[工具执行失败] 未知内置工具 {tool_name}"
        return text_content

    async def _obtain_mind_tools(self, mcp_servers, enable_web_search=False):
        tools = []

        # 内置搜索工具：按开关决定是否暴露给模型作为可选工具
        from toolmind.database.dao.web_search_config import WebSearchConfigDao
        user_config = await WebSearchConfigDao.get_config_by_user_id(self.user_id)
        
        if user_config:
            global_web_search_enabled = user_config.enabled
        else:
            global_web_search_enabled = True
            if getattr(app_settings, "tools", None) and getattr(
                app_settings.tools, "tavily", None
            ):
                global_web_search_enabled = app_settings.tools.tavily.get("enabled", True)

        if enable_web_search and global_web_search_enabled:
            tools.append(convert_to_openai_tool(web_search))

        async def get_mcp_tools():
            if self.mcp_tools:
                return self.mcp_tools

            servers_config = []
            # 记录每个 server 启用的工具名称，用于后续过滤
            enabled_tools = set()
            for mcp_id in mcp_servers:
                mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
                mcp_config = MCPConfig(**mcp_server)

                # mcp_config.tools 为空时表示「未初始化」或「全部可用」，保持兼容旧数据
                if mcp_config.tools:
                    enabled_tools.update(mcp_config.tools)
                    self.tool_mcp_server_dict.update(
                        {tool: mcp_config.mcp_server_id for tool in mcp_config.tools}
                    )
                servers_config.append(convert_mcp_config(mcp_config.model_dump()))
            self.mcp_manager = MCPManager(servers_config)
            all_mcp_tools = await self.mcp_manager.get_mcp_tools()

            # 如果有配置启用列表，则只暴露启用的工具；否则保持向后兼容，全部暴露
            if enabled_tools:
                filtered_tools = [
                    tool for tool in all_mcp_tools if tool.name in enabled_tools
                ]
            else:
                filtered_tools = all_mcp_tools
                # 兼容旧数据：为所有工具建立映射，避免 KeyError
                for mcp_id in mcp_servers:
                    mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
                    mcp_config = MCPConfig(**mcp_server)
                    for tool in filtered_tools:
                        self.tool_mcp_server_dict.setdefault(
                            tool.name, mcp_config.mcp_server_id
                        )

            self.mcp_tools = filtered_tools

            return filtered_tools

        mcp_tools = await get_mcp_tools()
        mcp_tools = [
            mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema)
            for tool in mcp_tools
        ]
        tools.extend(mcp_tools)

        return tools

    async def _record_agent_token_usage(
        self, response: AIMessage | AIMessageChunk | BaseMessage, model
    ):
        if response.usage_metadata:
            await UsageStatsService.create_usage_stats(
                model=model,
                user_id=self.user_id,
                agent=UsageStatsAgentType.mind_agent,
                input_tokens=response.usage_metadata.get("input_tokens"),
                output_tokens=response.usage_metadata.get("output_tokens"),
            )
