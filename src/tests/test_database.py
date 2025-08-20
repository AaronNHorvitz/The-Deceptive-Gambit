import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This import will fail until we create the database.py file
from gambit.database import Base, Game, get_or_create_game, log_move

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Create a temporary in-memory database session for a test."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_database_creation(db_session):
    """Tests that the database and tables can be created."""
    assert db_session is not None
    table_names = db_session.get_bind().table_names()
    assert "games" in table_names
    assert "moves" in table_names

def test_game_and_move_logging(db_session):
    """Tests logging a new game and a new move."""
    game = get_or_create_game(db_session, persona_name="NaiveNovice")
    assert game.id == 1

    move = log_move(
        session=db_session,
        game_id=game.id,
        turn_number=1,
        player="engine",
        move_notation="e2e4"
    )
    assert move.game_id == game.id
    assert len(game.moves) == 1