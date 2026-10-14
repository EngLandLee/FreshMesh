/* SPDX-License-Identifier: Apache-2.0 */
/* Copyright 2026 FreshMesh-DXOS contributors */
package com.freshmesh.workflow;

public final class WorkflowException extends RuntimeException {
    private final int status;
    private final String code;

    public WorkflowException(int status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }

    public int status() { return status; }
    public String code() { return code; }
}
