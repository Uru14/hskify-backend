from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, TIMESTAMP, text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column('userid', Integer, primary_key=True)
    name = Column('name', String)
    email = Column('email', String, unique=True)
    password_hash = Column('passwordhash', String)
    registration_date = Column('registrationdate', TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    progresses = relationship("Progress")
    scores = relationship("Score")
    user_achievements = relationship("UserAchievement")


class Character(Base):
    __tablename__ = 'characters'

    id = Column('characterid', Integer, primary_key=True)
    hanzi = Column('hanzi', String)
    pinyin = Column('pinyin', String)
    stroke_count = Column('strokecount', Integer)
    translation = Column('translation', String)
    hsk_level = Column('hsklevel', Integer)

    example_sentences = relationship("ExampleSentence")
    progresses = relationship("Progress")


class ExampleSentence(Base):
    __tablename__ = 'examplesentences'

    id = Column('sentenceid', Integer, primary_key=True)
    character_id = Column('characterid', Integer, ForeignKey('characters.characterid'))
    sentence = Column('sentence', String)
    translation = Column(String)


class Progress(Base):
    __tablename__ = 'progress'

    id = Column('progressid', Integer, primary_key=True)
    user_id = Column('userid', Integer, ForeignKey('users.userid'))
    character_id = Column('characterid', Integer, ForeignKey('characters.characterid'))
    learning_date = Column('learningdate', Date)
    is_favorite = Column('is_favorite', Boolean, default=False)


class Image(Base):
    __tablename__ = 'images'

    id = Column('imageid', Integer, primary_key=True)
    url = Column('url', String)
    description = Column('description', Text)


class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column('achievementid', Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', Text)
    criteria = Column('criteria', Text)
    image_id = Column('imageid', Integer, ForeignKey('images.imageid'))


class Game(Base):
    __tablename__ = 'games'

    id = Column('gameid', Integer, primary_key=True)
    name = Column('name', String)
    description = Column('description', Text)


class Score(Base):
    __tablename__ = 'scores'

    id = Column('scoreid', Integer, primary_key=True)
    game_id = Column('gameid', Integer, ForeignKey('games.gameid'))
    user_id = Column('userid', Integer, ForeignKey('users.userid'))
    score = Column('score', Integer)
    difficulty = Column('difficulty', String)
    parameters = Column('parameters', Text)


class UserAchievement(Base):
    __tablename__ = 'userachievements'

    id = Column('userachievementid', Integer, primary_key=True)
    user_id = Column('userid', Integer, ForeignKey('users.userid'))
    achievement_id = Column('achievementid', Integer, ForeignKey('achievements.achievementid'))
    obtained_date = Column('obtaineddate', Date)
