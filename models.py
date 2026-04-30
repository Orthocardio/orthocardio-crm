import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Numeric, JSON
from sqlalchemy.orm import relationship
from database import Base

class Contact(Base):
    __tablename__ = "contacts"

    phone_number = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    hospital = Column(String, nullable=True)
    is_ai_active = Column(Boolean, default=True)
    status = Column(String, default="PENDING")
    followup_draft = Column(String, nullable=True)
    last_interaction = Column(DateTime, default=datetime.datetime.utcnow)
    
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")
    quote_approvals = relationship("QuoteApproval", back_populates="contact", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    contact_phone = Column(String, ForeignKey("contacts.phone_number"))
    sender_type = Column(String) # 'user', 'ai', 'human', 'admin'
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)

    contact = relationship("Contact", back_populates="messages")

class QuoteApproval(Base):
    __tablename__ = "quote_approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    contact_phone = Column(String, ForeignKey("contacts.phone_number"))
    pdf_path = Column(String)
    status = Column(String, default="PENDING_APPROVAL") # DRAFT, PENDING_APPROVAL, APPROVED, MODIFICATION_REQUESTED
    items_json = Column(JSON) # Contiene los productos y precios propuestos
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    contact = relationship("Contact", back_populates="quote_approvals")

class PriceList(Base):
    __tablename__ = "price_list"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, unique=True, index=True)
    description = Column(String)
    price = Column(Numeric(12, 2))
    hospital = Column(String, nullable=True)
    alternative_code = Column(String, nullable=True)

class ClinicalKnowledge(Base):
    __tablename__ = "clinical_knowledge"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_code = Column(String, ForeignKey("price_list.code"))
    content = Column(String)
    embedding = Column(String, nullable=True) 
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
