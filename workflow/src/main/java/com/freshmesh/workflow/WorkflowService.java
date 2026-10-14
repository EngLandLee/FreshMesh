/* SPDX-License-Identifier: Apache-2.0 */
/* Copyright 2026 FreshMesh-DXOS contributors */
package com.freshmesh.workflow;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import org.flowable.engine.HistoryService;
import org.flowable.engine.RuntimeService;
import org.flowable.engine.TaskService;
import org.flowable.task.api.Task;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class WorkflowService {
    private static final String DEFINITION_KEY = "freshmesh-transfer";
    private final RuntimeService runtimeService;
    private final TaskService taskService;
    private final HistoryService historyService;
    private final JdbcTemplate jdbc;

    public WorkflowService(RuntimeService runtimeService, TaskService taskService,
                           HistoryService historyService, JdbcTemplate jdbc) {
        this.runtimeService = runtimeService;
        this.taskService = taskService;
        this.historyService = historyService;
        this.jdbc = jdbc;
    }

    @Transactional
    public ProcessStatus start(String businessKey) {
        if (businessKey == null || businessKey.isBlank()) {
            throw new WorkflowException(400, "invalid_business_key", "business_key là bắt buộc");
        }
        jdbc.query("SELECT pg_advisory_xact_lock(hashtext(?))",
                rs -> { rs.next(); return null; }, businessKey);
        String existing = findProcessId(businessKey);
        if (existing != null) {
            return status(existing);
        }
        var process = runtimeService.startProcessInstanceByKey(DEFINITION_KEY, businessKey);
        jdbc.update("INSERT INTO fm_workflow_process(business_key, process_id) VALUES (?, ?)",
                businessKey, process.getId());
        return status(process.getId());
    }

    @Transactional
    public ProcessStatus complete(String processId, CompleteRequest request) {
        if (processId == null || processId.isBlank()) {
            throw new WorkflowException(400, "invalid_process_id", "process_id là bắt buộc");
        }
        if (request == null || request.operationId() == null || request.operationId().isBlank()) {
            throw new WorkflowException(400, "invalid_operation_id", "operation_id là bắt buộc");
        }
        jdbc.query("SELECT pg_advisory_xact_lock(hashtext(?))",
                rs -> { rs.next(); return null; }, processId);
        String mapped = findProcessById(processId);
        if (mapped == null) {
            throw new WorkflowException(404, "process_not_found", "Không tìm thấy quy trình");
        }
        String operationProcess = jdbc.query("SELECT process_id FROM fm_workflow_operation WHERE operation_id = ?",
                rs -> rs.next() ? rs.getString(1) : null, request.operationId());
        if (operationProcess != null) {
            if (!operationProcess.equals(processId)) {
                throw new WorkflowException(409, "operation_reused", "operation_id đã được sử dụng");
            }
            return status(processId);
        }
        Task task = taskService.createTaskQuery().processInstanceId(processId).singleResult();
        if (task == null) {
            if (isEnded(processId)) {
                throw new WorkflowException(409, "process_ended", "Quy trình đã kết thúc");
            }
            throw new WorkflowException(409, "task_unavailable", "Không có bước đang chờ");
        }
        if (!Objects.equals(task.getTaskDefinitionKey(), request.task())) {
            throw new WorkflowException(409, "task_mismatch", "Bước quy trình không hợp lệ");
        }
        if ("approval".equals(request.task()) && request.approved() == null) {
            throw new WorkflowException(400, "approval_required", "approved là bắt buộc ở bước phê duyệt");
        }
        jdbc.update("INSERT INTO fm_workflow_operation(operation_id, process_id, task_key) VALUES (?, ?, ?)",
                request.operationId(), processId, task.getTaskDefinitionKey());
        Map<String, Object> variables = new HashMap<>();
        variables.put("last_actor", request.actor() == null ? "" : request.actor());
        variables.put("last_note", request.note() == null ? "" : request.note());
        variables.put("last_operation_id", request.operationId());
        if ("approval".equals(request.task())) {
            variables.put("approved", request.approved());
        }
        taskService.complete(task.getId(), variables);
        return status(processId);
    }

    @Transactional(readOnly = true)
    public ProcessStatus status(String processId) {
        if (findProcessById(processId) == null) {
            throw new WorkflowException(404, "process_not_found", "Không tìm thấy quy trình");
        }
        Task task = taskService.createTaskQuery().processInstanceId(processId).singleResult();
        return new ProcessStatus(processId, task == null ? null : task.getTaskDefinitionKey(), task == null && isEnded(processId));
    }

    private String findProcessId(String businessKey) {
        return jdbc.query("SELECT process_id FROM fm_workflow_process WHERE business_key = ?",
                rs -> rs.next() ? rs.getString(1) : null, businessKey);
    }

    private String findProcessById(String processId) {
        return jdbc.query("SELECT business_key FROM fm_workflow_process WHERE process_id = ?",
                rs -> rs.next() ? rs.getString(1) : null, processId);
    }

    private boolean isEnded(String processId) {
        var historic = historyService.createHistoricProcessInstanceQuery().processInstanceId(processId).singleResult();
        return historic != null && historic.getEndTime() != null;
    }

    public record CompleteRequest(String task, String operationId, Boolean approved, String actor, String note) { }
    public record ProcessStatus(@com.fasterxml.jackson.annotation.JsonProperty("process_id") String processId,
                                 String task, boolean ended) { }
}
