import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base

class Contact(Base):
    __tablename__ = "contacts"

    phone_number = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=True) # Especialidad o cargo
    hospital = Column(String, nullable=True) # Hospital de adscripción
    is_ai_active = Column(Boolean, default=True)
    last_interaction = Column(DateTime, default=datetime.datetime.utcnow)
    
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    contact_phone = Column(String, ForeignKey("contacts.phone_number"))
    sender_type = Column(String) # 'user', 'ai', o 'human'
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    contact = relationship("Contact", back_populates="messages")
