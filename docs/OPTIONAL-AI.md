# Optional AI profile

Copyright 2026 FreshMesh-DXOS contributors — SPDX-License-Identifier: Apache-2.0.

The core OLP workflow does not require AI. The optional `compose.ai.yaml` overlay
supplies a real Ollama service and `qwen2.5:0.5b` (Qwen2.5-0.5B-Instruct,
Apache-2.0 per its [model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)).
Weights remain in a Docker volume and are not included in the source release.

```sh
make up
make ai-up
```

`make ai-up` downloads the model and recreates the API with `OLLAMA_URL` and
`OLLAMA_MODEL`. Use the portal's “Trợ lý vận hành” action. CPU inference is
supported; speed and Vietnamese quality depend on hardware and this small model.
To return to core-only mode, run `make up`.

Before downloading a model, inspect its model card, license, acceptable-use terms,
retention behavior, and hardware requirements. Record the selected model and source
in the deployment change record. Model terms are separate from the Apache-2.0 terms
for FreshMesh source; see [LICENSES/INVENTORY.md](../LICENSES/INVENTORY.md).

If the endpoint or model is unavailable, `/api/agent/chat` returns a structured 503
and the portal shows an actionable unavailable state. AI output is advisory and must
never authorize a transfer, alter stock, or bypass tenant policy.
