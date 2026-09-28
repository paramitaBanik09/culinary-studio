# 🍳 Culinary Studio

An intelligent AI consultant built with the Google Agent Development Kit (ADK) that assists restaurant owners, chefs, and bistro operators in designing innovative menus, optimizing dish margins, generating visual plating mockups, and searching recipe inspirations.

![Culinary Studio Demo](./demo.gif)

---

## 🚀 Key Features & Implemented Capabilities

This project strictly implements the following tools, services, and Google Cloud integrations in `app/` and `agents-cli-manifest.yaml`:

### 1. **Firestore Menu Catalog Management**
- **`list_menu_items`**: Queries the Google Cloud Firestore `menu_items` collection by category to return catalog data.
- **`add_menu_item`**: Stores new dish entries into Firestore with names, descriptions, pricing, ingredient costs, and category classifications.

### 2. **Financial & Plate Costing Analysis**
- **`calculate_plate_cost`**: Performs cost-volume-profit math to calculate food cost percentage, dollar profit margin, and suggested menu retail pricing based on target margin goals.

### 3. **AI Image & Video Visual Mockups**
- **`generate_dish_image`**: Uses `gemini-3.1-flash-lite-image` via the Vertex AI Python SDK (`google-genai`) in the `global` region to generate presentation mockups. Saves artifacts via ADK `tool_context.save_artifact` and uploads images to Google Cloud Storage.
- **`generate_dish_video`**: Uses `gemini-omni-flash-preview` via the Vertex AI Interactions API in the `global` region to generate short video showcases. Saves artifacts to ADK and uploads `.mp4` video bytes to Cloud Storage.

### 4. **Cloud Storage Media Hosting**
- Automatically stores generated images and videos in Google Cloud Storage (`google-cloud-storage`) under public HTTPS URLs for inline UI rendering.

### 5. **Persistent Session Memory**
- **Vertex AI Memory Bank Service**: Integrates `google.adk.memory.vertex_ai_memory_bank_service.VertexAiMemoryBankService` to persist restaurant context, user preferences, and menu history across conversation turns.

### 6. **External Recipe Search**
- **`search_recipe_inspiration`**: Queries the external `TheMealDB` API for culinary dish references, ingredient combinations, and preparation techniques.

### 7. **A2UI Protocol Renders (v0.8 Basic Catalog)**
- Uses `A2uiSchemaManager` (version 0.8) and `a2ui_callback` to format agent responses into rich, structured UI components (Cards, Columns, Rows, Images) for chat frontends.

---

## 📋 Planned / Not Yet Implemented Capabilities

The following features were outlined in initial design concepts but are **not yet implemented**:
- ❌ Direct integration with Point-of-Sale (POS) systems (e.g., Toast, Square).
- ❌ Automated supplier purchase order generation and real-time inventory tracking.

---

## 🛠️ Architecture & Google Cloud Stack

- **Agent Framework**: Google Agent Development Kit (`google-adk`)
- **Deployment Platform**: Vertex AI Reasoning Engine / Agent Runtime (`agents-cli deploy`)
- **Database**: Google Cloud Firestore
- **Object Storage**: Google Cloud Storage (GCS)
- **Generative AI Models**:
  - `gemini-flash-latest` (Root Agent Reasoning)
  - `gemini-3.1-flash-lite-image` (Dish Image Generation)
  - `gemini-omni-flash-preview` (Dish Video Generation via Interactions API)
- **Frontend / Proxy**: FastAPI server with plain HTML/JS chat frontend and category prompt tabs.

---

## 💻 Local Setup & Run Instructions

### Prerequisites
- Python 3.10+
- `gcloud` CLI configured with an active GCP project
- Google Cloud permissions for Firestore, Cloud Storage, and Vertex AI

### 1. Installation

Clone the repository and install dependencies:

```bash
# Install Python dependencies
uv pip install -r app/requirements.txt
```

### 2. Environment Setup

Set the necessary environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-east1"
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT_NUMBER/locations/us-east1/reasoningEngines/YOUR_ENGINE_ID"
export AGENT_DIRECTORY="app"
```

### 3. Running the Frontend Proxy Locally

Start the local FastAPI proxy and web frontend:

```bash
cd frontend
python3 main.py
```
