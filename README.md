# Milu

Simple Agentic AI prototype that calls an OpenAI-compatible LLM and exposes a Telegram interface.

## Overview

Milu is a small prototype demonstrating patterns for Agentic AI. Right now it:

- Makes API calls to an OpenAI-compatible LLM (set via environment variable).
- Provides a Telegram bot interface for interacting with the agent.

The project is intentionally minimal so you can experiment with agent patterns and extend behavior.

## Requirements

- Python 3.10+ (or compatible)
- Docker (for container builds)
- kubectl (for Kubernetes deployment)

## Quickstart — Local (venv)

1. Create a virtual environment and activate it:

	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```

2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Set required environment variables (example):

	```bash
	export OPENAI_API_KEY="sk-..."
	export TELEGRAM_BOT_TOKEN="123456:ABC-..."
	# Optionally set TELEGRAM_CHAT_ID if you want messages routed to a single chat
	export TELEGRAM_CHAT_ID="..."
	```

4. Run the app locally:

	```bash
	python milu.py
	```

The application will start and listen (see `milu.py` for details). Use the Telegram bot to interact.

## Running in Kubernetes

There is a sample Kubernetes manifest in `kubernetes.yaml`. Basic steps:

1. Build and push a Docker image for the app (example, replace tags and registry):

	```bash
	docker build -t your-registry/milu:latest .
	docker push your-registry/milu:latest
	```

2. Create a Kubernetes secret with your runtime keys:

	```bash
	kubectl create secret generic milu-secrets \
	  --from-literal=OPENAI_API_KEY="sk-..." \
	  --from-literal=TELEGRAM_BOT_TOKEN="123456:ABC-..."
	```

3. Edit `kubernetes.yaml` to use your image `your-registry/milu:latest` and confirm it references the `milu-secrets` secret for env vars.

4. Apply the manifest:

	```bash
	kubectl apply -f kubernetes.yaml
	```

5. Monitor pods and logs:

	```bash
	kubectl get pods
	kubectl logs -f deployment/milu
	```

Adjust service and ingress settings as needed for your cluster.

## What it does today

- Uses the OpenAI API (or compatible) to perform LLM calls from `milu.py`.
- Exposes a Telegram bot so you can send messages and receive agent responses.

## Purpose

This repository is intended as a playground to implement and experiment with Agentic AI patterns (chaining, planning, tool use, memory, etc.). Keep things small and iterative here.

## Contributing

Feel free to open issues or PRs. If you add features that require configuration, update this README with clear setup steps.

## License

MIT-style (add your preferred license file)

