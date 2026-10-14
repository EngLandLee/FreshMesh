-- SPDX-License-Identifier: Apache-2.0
-- Copyright 2026 FreshMesh-DXOS contributors
CREATE TABLE IF NOT EXISTS fm_workflow_process (
  business_key VARCHAR(255) PRIMARY KEY,
  process_id VARCHAR(64) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fm_workflow_operation (
  operation_id VARCHAR(255) PRIMARY KEY,
  process_id VARCHAR(64) NOT NULL,
  task_key VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_fm_workflow_operation_process
  ON fm_workflow_operation(process_id);
