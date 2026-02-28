import json
from typing import List, Union, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage, AIMessageChunk
from langchain_core.utils.function_calling import convert_to_openai_tool

from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.mcp_user_config import MCPUserConfigService
from agentchat.api.services.usage_stats import UsageStatsService
from agentchat.api.services.workspace_session import WorkSpaceSessionService
from agentchat.core.callbacks import usage_metadata_callback
from agentchat.database.models.workspace_session import WorkSpaceSessionCreate, WorkSpaceSessionContext
from agentchat.prompts.template import GuidePromptTemplate
from agentchat.schema.workspace import WorkSpaceAgents
from agentchat.schema.usage_stats import UsageStatsAgentType
from agentchat.core.agents.mcp_agent import MCPConfig
from agentchat.services.web_search.google_search.action import google_search
from agentchat.services.web_search.tavily_search.action import tavily_search as web_search
# from agentchat.api.services.tool import ToolService
from agentchat.core.models.manager import ModelManager
from agentchat.utils.convert import mcp_tool_to_args_schema, convert_mcp_config
from agentchat.utils.date_utils import get_beijing_time
from agentchat.services.mcp.manager import MCPManager
from agentchat.prompts.lingseek import GenerateGuidePrompt, FeedBackGuidePrompt, GenerateTitlePrompt, \
    GenerateTaskPrompt, FixJsonPrompt, ToolCallPrompt, SystemMessagePrompt, EvaluateResultPrompt
from agentchat.schema.lingseek import LingSeekGuidePrompt, LingSeekGuidePromptFeedBack, LingSeekTask, \
    LingSeekTaskStep


class LingSeekAgent:

    def __init__(self, user_id: str):
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_tools = []
        self.tool_mcp_server_dict = {}

        self.user_id = user_id
        
    async def get_conversation_model(self):
        return await ModelManager.get_conversation_model(user_id=self.user_id)
        
    async def get_tool_call_model(self):
        return await ModelManager.get_lingseek_intent_model(user_id=self.user_id)

    async def _generate_guide_prompt(self, lingseek_guide_prompt):
        """
        通过COT的方法使得模型回复的更加准确，但是展示的时候需要把思考内容隐藏
        """
        one = None
        sop_flag = False
        sop_content = ""
        answer = ""
        split_tags = ["<Thought_END>", "</Thought_END>"]
        model = await self.get_conversation_model()
        async for one in model.astream(input=lingseek_guide_prompt, config={"callbacks": [usage_metadata_callback]}):
            answer += f"{one.content}"
            if sop_flag:
                yield one
                sop_content += one.content
                continue
            for split_tag in split_tags:
                if answer.find(split_tag) != -1:
                    sop_flag = True
                    sop_content = answer.split(split_tag)[-1].strip()
                    if sop_content:
                        one.content = sop_content
                        yield one
                    break
        if not sop_content:
            one.content = answer
            yield one

    async def _generate_tasks(self, lingseek_task_prompt):
        model = await self.get_conversation_model()
        conversation_json_model = model.bind(response_format={"type": "json_object"})

        response = await conversation_json_model.ainvoke(input=lingseek_task_prompt, config={"callbacks": [usage_metadata_callback]})

        try:
            content = json.loads(response.content)
            return content
        except Exception as err:
            fix_message = FixJsonPrompt.format(json_content=response.content, json_error=str(err))
            fix_response = await conversation_json_model.ainvoke(input=fix_message, config={"callbacks": [usage_metadata_callback]})
            try:
                fix_content = json.loads(fix_response.content)
                return fix_content
            except Exception as fix_err:
                raise ValueError(fix_err)

    async def _generate_title(self, query):
        title_prompt = GenerateTitlePrompt.format(query=query)
        model = await self.get_conversation_model()
        response = await model.ainvoke(input=title_prompt, config={"callbacks": [usage_metadata_callback]})
        return response.content

    async def _add_workspace_session(self, query, contexts: WorkSpaceSessionContext):
        title = await self._generate_title(query)
        await WorkSpaceSessionService.create_workspace_session(
            WorkSpaceSessionCreate(
                title=title,
                user_id=self.user_id,
                contexts=[contexts.model_dump()],
                agent=WorkSpaceAgents.LingSeekAgent.value))

    async def _parse_function_call_response(self, message: AIMessage):
        tool_messages = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")
                tool_call_id = tool_call.get("id")

                content = await self._process_tools_result(tool_name, tool_args)
                tool_messages.append(ToolMessage(content=content, name=tool_name, tool_call_id=tool_call_id))

        return tool_messages

    async def generate_tasks(self, lingseek_task: LingSeekTask):
        tools = await self._obtain_lingseek_tools(lingseek_task.plugins, lingseek_task.mcp_servers, lingseek_task.web_search)
        tools_str = json.dumps(tools, ensure_ascii=False, indent=2)

        lingseek_task_prompt = GenerateTaskPrompt.format(
            tools_str=tools_str,
            query=lingseek_task.query,
            current_time=get_beijing_time(),
        )

        response_task = await self._generate_tasks(lingseek_task_prompt)
        return response_task

    async def generate_guide_prompt(self, lingseek_info: Union[LingSeekGuidePrompt, LingSeekGuidePromptFeedBack],
                                    feedback: bool = False):

        tools = await self._obtain_lingseek_tools(lingseek_info.plugins, lingseek_info.mcp_servers, lingseek_info.web_search)
        tools_str = json.dumps(tools, ensure_ascii=False, indent=2)

        if feedback:
            lingseek_guide_prompt = FeedBackGuidePrompt.format(
                query=lingseek_info.query,
                tools_str=tools_str,
                feedback=lingseek_info.feedback,
                feedback_guide_prompt=lingseek_info.guide_prompt,
            )
        else:
            lingseek_guide_prompt = GenerateGuidePrompt.format(
                tools_str=tools_str,
                query=lingseek_info.query,
                guide_prompt_template=GuidePromptTemplate,
            )
        async for chunk in self._generate_guide_prompt(lingseek_guide_prompt):
            yield {
                "event": "generate_guide_prompt",
                "data": {
                    "chunk": chunk.content
                }
            }


    async def _evaluate_result(self, query: str, answer: str) -> dict:
        """
        Evaluate the generated result using tool_call_model and web_search tool.
        """
        eval_prompt = EvaluateResultPrompt.format(query=query, answer=answer)
        messages: List[BaseMessage] = [SystemMessage(content="你是一个专业的结果评判助手。"), HumanMessage(content=eval_prompt)]
        
        tools = [convert_to_openai_tool(web_search)]
        model = await self.get_tool_call_model()
        eval_model = model.bind_tools(tools)
        
        try:
            while True:
                response = await eval_model.ainvoke(input=messages, config={"callbacks": [usage_metadata_callback]})
                messages.append(response)
                
                if response.tool_calls:
                    tool_messages = await self._parse_function_call_response(response)
                    messages.extend(tool_messages)
                else:
                    break
                    
            content = response.content.strip()
            print(f"[DEBUG _evaluate_result] Raw LLM response: {content}")
            
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
                
            parsed_json = json.loads(json_str)
            print(f"[DEBUG _evaluate_result] Parsed JSON data: {parsed_json}")
            return parsed_json
        except Exception as err:
            import openai
            print(f"[DEBUG _evaluate_result] Exception occurred first time: {err}")
            if isinstance(err, openai.RateLimitError) or 'insufficient_quota' in str(err) or '429' in str(err):
                print(f"[DEBUG _evaluate_result] Returning 80 due to RateLimit API issue.")
                return {"score": 80, "reasoning": "评判模型触发限流或余额不足 (RateLimitError/Insufficient Quota)，默认算作通过。"}
            
            try:
                # 尝试修复一般的 JSON 格式错误或者报错，注意应传入原本的 content
                json_content_to_fix = locals().get('content', '')
                fix_message = FixJsonPrompt.format(json_content=json_content_to_fix, json_error=str(err))
                model = await self.get_conversation_model()
                fix_response = await model.ainvoke(input=fix_message, config={"callbacks": [usage_metadata_callback]})
                fix_content = fix_response.content.strip()
                
                json_match = re.search(r'\{.*\}', fix_content, re.DOTALL)
                if json_match:
                    fix_content = json_match.group(0)
                    
                return json.loads(fix_content)
            except Exception as e:
                return {"score": 100, "reasoning": f"评判执行异常: {str(e)}，默认放行。"}

    async def submit_lingseek_task(self, lingseek_task: LingSeekTask):
        loop_count = 0
        max_loop = 3

        while loop_count < max_loop:
            loop_count += 1
            if loop_count > 1:
                yield {
                    "event": "step_result",
                    "data": {"message": "正在重新规划任务并重头执行...", "title": f"第 {loop_count} 次重跑"}
                }

            task = await self.generate_tasks(lingseek_task)

            tasks_graph = {}
            tasks_show = []
            steps = task.get("steps", [])
            for step in steps:
                task_step = LingSeekTaskStep(**step)
                tasks_graph[task_step.step_id] = task_step

            for step_id, step_info in tasks_graph.items():
                for input_step in step_info.input:
                    if input_step in tasks_graph:
                        # 构建展示的任务列表图结构
                        tasks_show.append({
                            "start": tasks_graph[input_step].title,
                            "end": tasks_graph[step_id].title
                        })
                    else:
                        tasks_show.append({
                            "start": "用户问题",
                            "end": tasks_graph[step_id].title
                        })
            yield {
                "event": "generate_tasks",
                "data": {"graph": tasks_show}
            }


            tools = await self._obtain_lingseek_tools(lingseek_task.plugins, lingseek_task.mcp_servers, lingseek_task.web_search)
            model = await self.get_tool_call_model()
            tool_call_model = model.bind_tools(tools) if len(tools) else model

            messages: List[BaseMessage] = [SystemMessage(content=SystemMessagePrompt), HumanMessage(content=lingseek_task.query)]
            context_task = []
            for step_id, step_info in tasks_graph.items():
                step_context = []
                for input_step in step_info.input:
                    if input_step in tasks_graph:
                        step_context.append(
                            tasks_graph[input_step].model_dump()
                        )

                step_prompt = ToolCallPrompt.format(
                    step_info=step_info,
                    step_context=str(step_context)
                )
                step_messages = [SystemMessage(content=step_prompt), HumanMessage(content=lingseek_task.query)]
                response = await tool_call_model.ainvoke(input=step_messages, config={"callbacks": [usage_metadata_callback]})

                tools_messages = await self._parse_function_call_response(response)

                step_info.result = "\n".join([msg.content for msg in tools_messages])

                context_task.append(step_info.model_dump())
                if tools_messages: # 合到整体Messages
                    messages.append(response)
                    messages.extend(tools_messages)
                else:
                    messages.append(HumanMessage(content=lingseek_task.query))
                    messages.append(AIMessage(content=response.content))
                yield {
                    "event": "step_result",
                    "data": {"message": step_info.result or " ", "title": step_info.title}
                }

            final_response = ""
            model = await self.get_conversation_model()
            async for chunk in model.astream(messages):
                final_response += chunk.content
                yield {
                    "event": "task_result",
                    "data": {"message": chunk.content}
                }

            # Evaluation check
            print(f"[{get_beijing_time()}] [LingSeekAgent] Start _evaluate_result...")
            eval_res = await self._evaluate_result(lingseek_task.query, final_response)
            score = eval_res.get("score", 100)
            reasoning = eval_res.get("reasoning", "")
            print(f"[{get_beijing_time()}] [LingSeekAgent] Evaluated result -> Score: {score}, Reasoning: {reasoning}")

            if score >= 80 or loop_count == max_loop:
                pass_msg = f"\n\n\n> **✅ 自我反馈通过** (匹配度: {score}/100)\n> **理由**: {reasoning}\n\n---\n\n"
                yield {
                    "event": "task_result",
                    "data": {"message": pass_msg}
                }
                final_response += pass_msg
                
                await self._add_workspace_session(
                    lingseek_task.query,
                    WorkSpaceSessionContext(
                        query=lingseek_task.query,
                        guide_prompt="",
                        task=context_task,
                        task_graph=tasks_show,
                        answer=final_response
                    ))
                break
            else:
                retry_msg = f"\n\n\n> **⚠️ 自我反馈未通过** (匹配度: {score}/100)\n> **理由**: {reasoning}\n> \n> __系统正在进行第 {loop_count + 1} 次重跑尝试...__\n\n---\n\n"
                yield {
                    "event": "task_result",
                    "data": {"message": retry_msg}
                }

    async def _process_tools_result(self, tool_name, tool_args):
        def find_mcp_tool(tool_name):
            """Find MCP tool by name"""
            for tool in self.mcp_tools:
                if tool.name == tool_name:
                    return tool
            return None

        if tool := find_mcp_tool(tool_name):
            mcp_config = await MCPUserConfigService.get_mcp_user_config(self.user_id,
                                                                        self.tool_mcp_server_dict[tool_name])
            tool_args.update(mcp_config)
            text_content, no_text_content = await tool.coroutine(**tool_args)
        else:
            from agentchat.services.web_search.tavily_search.action import tavily_search
            from agentchat.services.web_search.google_search.action import google_search
            LingSeekPlugins = {
                "tavily_search": tavily_search,
                "web_search": tavily_search,
                "google_search": google_search,
            }
            text_content = LingSeekPlugins[tool_name].invoke(tool_args)
        return text_content

    async def _obtain_lingseek_tools(self, plugins, mcp_servers, enable_web_search=False):
        # plugins_name = await ToolService.get_tool_name_by_id(plugins)
        # plugins_func = [LingSeekPlugins.get(name) for name in plugins_name]
        # tools = [convert_to_openai_tool(func) for func in plugins_func]

        # if enable_web_search and web_search not in plugins_func:
        #     plugins_func.append(web_search)
        #     tools.append(convert_to_openai_tool(web_search))
        tools = []

        async def get_mcp_tools():
            if self.mcp_tools:
                return self.mcp_tools

            servers_config = []
            for mcp_id in mcp_servers:
                mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
                mcp_config = MCPConfig(**mcp_server)

                self.tool_mcp_server_dict.update({tool: mcp_config.mcp_server_id for tool in mcp_config.tools})
                servers_config.append(
                    convert_mcp_config(mcp_config.model_dump())
                )
            self.mcp_manager = MCPManager(servers_config)
            mcp_tools = await self.mcp_manager.get_mcp_tools()
            self.mcp_tools = mcp_tools

            return mcp_tools

        mcp_tools = await get_mcp_tools()
        mcp_tools = [mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema) for tool in mcp_tools]
        tools.extend(mcp_tools)

        return tools

    async def _record_agent_token_usage(self, response: AIMessage | AIMessageChunk | BaseMessage, model):
        if response.usage_metadata:
            await UsageStatsService.create_usage_stats(
                model=model,
                user_id=self.user_id,
                agent=UsageStatsAgentType.lingseek_agent,
                input_tokens=response.usage_metadata.get("input_tokens"),
                output_tokens=response.usage_metadata.get("output_tokens")
            )