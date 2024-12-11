# Secret Friend Generator

Secret Friend Generator is a basic FastAPI application that allows users to manage and generate secret friend events.

## Features

- Create and manage secret friend events
- Add participants to events
- Randomly generate secret friend assignments

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/secret-friend-generator.git
   cd secret-friend-generator
   ```

2. Install dependencies using Poetry:

   ```bash
   poetry install
   ```

## Running the Application

1. Start the FastAPI server:

   ```bash
   poetry run dev
   ```

2. Access the application at `http://127.0.0.1:8000`.

## API Endpoints

- `GET /events`: Retrieve a list of all secret friend events.
- `POST /events`: Create a new secret friend event.
- `GET /events/{event_id}`: Retrieve details of a specific event.
- `POST /events/{event_id}/participants`: Add participants to an event.
- `POST /events/{event_id}/generate`: Generate secret friend assignments for an event.

## License

This project is licensed under the MIT License.
