from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        ForeignKey, Boolean, Text)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    persona_name = Column(String, nullable=False)
    status = Column(String, default="in_progress")
    final_outcome = Column(String)
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")

class Move(Base):
    __tablename__ = 'moves'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    turn_number = Column(Integer, nullable=False)
    player = Column(String, nullable=False)
    move_notation = Column(String)
    is_legal = Column(Boolean)
    board_state_fen = Column(String)
    engine_evaluation = Column(Float)
    persona_commentary = Column(Text)
    llm_commentary = Column(Text)
    game = relationship("Game", back_populates="moves")

def get_or_create_game(session, persona_name: str) -> Game:
    new_game = Game(persona_name=persona_name)
    session.add(new_game)
    session.commit()
    return new_game

def log_move(session, game_id: int, **kwargs) -> Move:
    new_move = Move(game_id=game_id, **kwargs)
    session.add(new_move)
    session.commit()
    return new_move

def init_db(db_path: str):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session