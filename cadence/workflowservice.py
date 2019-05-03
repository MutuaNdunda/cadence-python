from __future__ import annotations

from typing import Tuple
from uuid import uuid4

import os
import socket

from cadence.thrift import cadence
from cadence.connection import TChannelConnection, ThriftFunctionCall
from cadence.errors import find_error
from cadence.conversions import copy_thrift_to_py, copy_py_to_thrift
from cadence.types import PollForActivityTaskResponse, StartWorkflowExecutionRequest, StartWorkflowExecutionResponse, \
    RegisterDomainRequest, PollForActivityTaskRequest, RespondActivityTaskCompletedRequest, DescribeTaskListResponse, \
    DescribeWorkflowExecutionRequest, DescribeWorkflowExecutionResponse, QueryWorkflowRequest, QueryWorkflowResponse, \
    ResetStickyTaskListResponse, ResetStickyTaskListRequest, RespondQueryTaskCompletedRequest, \
    ListClosedWorkflowExecutionsResponse, ListClosedWorkflowExecutionsRequest, ListOpenWorkflowExecutionsRequest, \
    ListOpenWorkflowExecutionsResponse, TerminateWorkflowExecutionRequest, SignalWithStartWorkflowExecutionRequest, \
    SignalWorkflowExecutionRequest, RequestCancelWorkflowExecutionRequest, RespondActivityTaskCanceledByIDRequest, \
    RespondActivityTaskCanceledRequest, RespondActivityTaskFailedByIDRequest, RespondActivityTaskFailedRequest

TCHANNEL_SERVICE = "cadence-frontend"


class WorkflowService:

    @classmethod
    def create(cls, host: str, port: int):
        connection = TChannelConnection.open(host, port)
        return cls(connection)

    @classmethod
    def get_identity(self):
        return "%d@%s" % (os.getpid(), socket.gethostname())

    def __init__(self, connection: TChannelConnection):
        self.connection = connection
        self.execution_start_to_close_timeout_seconds = 86400
        self.task_start_to_close_timeout_seconds = 120

    def thrift_call(self, method_name, request_argument):
        thrift_request_argument = copy_py_to_thrift(request_argument)
        fn = getattr(cadence.WorkflowService, method_name, None)
        assert fn
        request = fn.request(thrift_request_argument)
        request_payload = cadence.dumps(request)
        call = ThriftFunctionCall.create(TCHANNEL_SERVICE, "WorkflowService::" + method_name, request_payload)
        response = self.connection.call_function(call)
        start_response = cadence.loads(fn.response, response.thrift_payload)
        return start_response

    def call_return(self, method_name: str, request: object, expected_return_type: type) -> Tuple[object, object]:
        response = self.thrift_call(method_name, request)
        if not response.success:
            return None, find_error(response)
        return_value = copy_thrift_to_py(response.success)
        assert isinstance(return_value, expected_return_type)
        return return_value, None

    def call_void(self, method_name, request):
        response = self.thrift_call(method_name, request)
        error = find_error(response)
        return None, error

    def start_workflow(self, request: StartWorkflowExecutionRequest) -> Tuple[StartWorkflowExecutionResponse, object]:
        return self.call_return("StartWorkflowExecution", request, StartWorkflowExecutionResponse)

    def register_domain(self, request: RegisterDomainRequest) -> [None, object]:
        return self.call_void("RegisterDomain", request)

    def poll_for_activity_task(self, request: PollForActivityTaskRequest) -> Tuple[PollForActivityTaskResponse, object]:
        return self.call_return("PollForActivityTask", request, PollForActivityTaskResponse)

    def respond_activity_task_failed(self, request: RespondActivityTaskFailedRequest) -> Tuple[None, object]:
        return self.call_void("RespondActivityTaskFailed", request)

    def respond_activity_task_failed_by_id(self, request: RespondActivityTaskFailedByIDRequest) -> Tuple[None, object]:
        return self.call_void("RespondActivityTaskFailedByID", request)

    def respond_activity_task_canceled(self, request: RespondActivityTaskCanceledRequest) -> Tuple[None, object]:
        return self.call_void("RespondActivityTaskCanceled", request)

    def respond_activity_task_canceled_by_id(self, request: RespondActivityTaskCanceledByIDRequest) -> \
        Tuple[None, object]:
        return self.call_void("RespondActivityTaskCanceledByID", request)

    def request_cancel_workflow_execution(self, request: RequestCancelWorkflowExecutionRequest) -> \
            Tuple[None, object]:
        return self.call_void("RequestCancelWorkflowExecution", request)

    def signal_workflow_execution(self, request: SignalWorkflowExecutionRequest) -> Tuple[None, object]:
        return self.call_void("SignalWorkflowExecution", request)

    def signal_with_start_workflow_execution(self, request: SignalWithStartWorkflowExecutionRequest) -> \
            Tuple[StartWorkflowExecutionResponse, object]:
        return self.call_return("SignalWithStartWorkflowExecution", request, StartWorkflowExecutionResponse)

    def respond_activity_task_completed(self, request: RespondActivityTaskCompletedRequest) -> Tuple[None, object]:
        return self.call_void("RespondActivityTaskCompleted", request)

    def terminate_workflow_execution(self, request: TerminateWorkflowExecutionRequest) -> Tuple[None, object]:
        return self.call_void("TerminateWorkflowExecution", request)

    def list_open_workflow_executions(self, request: ListOpenWorkflowExecutionsRequest) -> \
            Tuple[ListOpenWorkflowExecutionsResponse, object]:
        return self.call_return("ListOpenWorkflowExecutions", request, ListOpenWorkflowExecutionsResponse)

    def list_closed_workflow_executions(self, request: ListClosedWorkflowExecutionsRequest) -> \
            Tuple[ListClosedWorkflowExecutionsResponse, object]:
        return self.call_return("ListClosedWorkflowExecutions", request, ListClosedWorkflowExecutionsResponse)

    def respond_query_task_completed(self, request: RespondQueryTaskCompletedRequest) -> Tuple[None, object]:
        return self.call_void("RespondQueryTaskCompleted", request)

    def reset_sticky_task_list(self, request: ResetStickyTaskListRequest) -> Tuple[ResetStickyTaskListResponse, object]:
        return self.call_return("ResetStickyTaskList", request, ResetStickyTaskListResponse)

    def query_workflow(self, request: QueryWorkflowRequest) -> Tuple[QueryWorkflowResponse, object]:
        return self.call_return("QueryWorkflow", request, QueryWorkflowResponse)

    def describe_workflow_execution(self, request: DescribeWorkflowExecutionRequest) -> Tuple[DescribeWorkflowExecutionResponse, object]:
        return self.call_return("DescribeWorkflowExecution", request, DescribeWorkflowExecutionResponse)

    def describe_task_list(self, request) -> Tuple[DescribeTaskListResponse, object]:
        return self.call_return("DescribeTaskList", request, DescribeTaskListResponse)
