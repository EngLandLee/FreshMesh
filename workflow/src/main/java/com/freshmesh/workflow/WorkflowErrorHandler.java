/* SPDX-License-Identifier: Apache-2.0 */
/* Copyright 2026 FreshMesh-DXOS contributors */
package com.freshmesh.workflow;

import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class WorkflowErrorHandler {
    @ExceptionHandler(WorkflowException.class)
    public ResponseEntity<Map<String, Object>> workflow(WorkflowException exception) {
        return ResponseEntity.status(exception.status()).body(Map.of(
                "error", Map.of("code", exception.code(), "message_vi", exception.getMessage())));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> invalid(MethodArgumentNotValidException exception) {
        return ResponseEntity.badRequest().body(Map.of(
                "error", Map.of("code", "invalid_request", "message_vi", "Dữ liệu yêu cầu không hợp lệ")));
    }
}
