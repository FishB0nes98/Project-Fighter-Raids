# Project Fighter Raids

A Python-based fighting game with raid mechanics, character progression, and multiplayer features.

## Features

- Multiple playable characters with unique abilities
- Raid system with different stages and difficulties
- Character progression and inventory system
- User authentication and profile management
- Real-time multiplayer combat
- Special effects and modifiers

## Prerequisites

- Python 3.12+
- Poetry for dependency management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Project-Fighter-Raids.git
cd Project-Fighter-Raids
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up your environment variables:
   - Create a `.env` file in the root directory
   - Add necessary configuration (see `.env.example`)

## Running the Game

```bash
poetry run python main.py
```

## Project Structure

- `abilities/`: Character abilities and special moves
- `characters/`: Character classes and attributes
- `config/`: Configuration files
- `engine/`: Core game engine and mechanics
- `gui/`: User interface components
- `items/`: In-game items and inventory system
- `services/`: Backend services and API integrations
- `stages/`: Game stages and raid levels
- `utils/`: Utility functions and helpers

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 