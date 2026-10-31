FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       git \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ENV UV_INSTALL_DIR="/root/.local"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="${UV_INSTALL_DIR}/bin:${PATH}"

RUN curl -fsSL https://opencode.ai/install | bash