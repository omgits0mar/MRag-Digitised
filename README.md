# MRag-Digitised

Multilingual RAG project workspace for the MRAG platform.

## Contents

- Project planning and specification artifacts
- Natural Questions filtered dataset
- Assignment brief and supporting documentation
- Speckit and agent workflow files used to structure implementation
- Backend application code under `src/mrag/`
- Frontend SPA workspace under `frontend/`

## Frontend Workflow

Use the shared `mrag` conda environment for both backend and frontend work in this repository.
The frontend toolchain is installed inside that environment, so the normal loop is:

```bash
conda activate mrag
cd frontend
npm install
npm run dev
```

Key frontend commands:

- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run build:check`

Feature-specific frontend documentation lives in [frontend/README.md](/Users/omar/Projects/Interview_Assesments/Digitised/frontend/README.md).
