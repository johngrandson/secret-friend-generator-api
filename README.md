# Secret Friend Generator API

This project is a Secret Friend Generator API that allows users to create and manage secret friend events.

## Getting Started

### Prerequisites

Make sure you have the following installed on your machine:

- [Python](https://www.python.org/) (version 3.8 or higher)
- [Poetry](https://python-poetry.org/) (version 1.1.0 or higher)

### Project Setup

Clone the repository:

```bash
git clone https://github.com/johngrandson/secret-friend-generator-api.git
```

Navigate to the project directory:

```bash
cd secret-friend-generator-api
```

Load the virtual environment:

```bash
poetry shell
```

Install the dependencies:

```bash
poetry install
```

### Running the Project

Navigate to the `docker` directory:

```bash
cd docker
```

Start the services using `docker-compose`:

```bash
docker-compose up -d
```


Start the development server:

```bash
poetry run start
```

The API will be running at `http://localhost:8000`.


### Running Tests

To run the tests, use the following command:

```bash
poetry run pytest
```

### API Documentation

The API documentation is available at `http://localhost:8000/docs` once the server is running.

### Contributing

If you would like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Contact

If you have any questions or suggestions, feel free to open an issue or contact the project maintainers.