/* SPDX-License-Identifier: Apache-2.0 */
/* Copyright 2026 FreshMesh-DXOS contributors */
package com.freshmesh.workflow;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping
public class WorkflowController {
    private final WorkflowService service;

    public WorkflowController(WorkflowService service) {
        this.service = service;
    }

    @GetMapping("/health")
    public Health health() {
        return new Health("ok");
    }

    @PostMapping("/processes")
    public WorkflowService.ProcessStatus start(@Valid @RequestBody StartRequest request) {
        return service.start(request.businessKey());
    }

    @GetMapping("/processes/{id}")
    public WorkflowService.ProcessStatus status(@PathVariable String id) {
        return service.status(id);
    }

    @PostMapping("/processes/{id}/complete")
    public WorkflowService.ProcessStatus complete(@PathVariable String id,
                                                   @Valid @RequestBody CompleteRequest request) {
        return service.complete(id, new WorkflowService.CompleteRequest(
                request.task(), request.operationId(), request.approved(), request.actor(), request.note()));
    }

    public record Health(String status) { }
    public record StartRequest(@NotBlank @JsonProperty("business_key") String businessKey) { }
    public record CompleteRequest(
            @NotBlank String task,
            @NotBlank @JsonProperty("operation_id") String operationId,
            Boolean approved,
            @NotBlank String actor,
            String note) { }
}
