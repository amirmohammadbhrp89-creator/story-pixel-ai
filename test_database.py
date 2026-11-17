from app.database.projects import create_project, get_projects
from app.database.episodes import create_episode, get_episodes
from app.database.characters import create_character, get_characters

# Create project
project_id = create_project(
    "Test Project",
    "animation",
    "Database test"
)

# Create episode
episode_id = create_episode(
    project_id,
    1,
    "Episode One",
    "First test episode"
)

# Create character
character_id = create_character(
    project_id,
    "Test Character",
    "First test character"
)

# Read data
print("\nPROJECTS:")
for project in get_projects():
    print(dict(project))

print("\nEPISODES:")
for episode in get_episodes(project_id):
    print(dict(episode))

print("\nCHARACTERS:")
for character in get_characters(project_id):
    print(dict(character))

print("\nDATABASE TEST SUCCESSFUL!")