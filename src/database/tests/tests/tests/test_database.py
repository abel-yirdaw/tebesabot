"""
Database tests for Habesha Dating Bot
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.database.supabase_client import supabase
from src.database.models_sql import SQL_SCHEMA

class TestDatabase:
    """Test database operations"""
    
    @patch('src.database.supabase_client.create_client')
    def test_supabase_initialization(self, mock_create):
        """Test Supabase client initialization"""
        mock_create.return_value = Mock()
        client = supabase
        assert client is not None
    
    def test_sql_schema(self):
        """Test SQL schema contains required tables"""
        assert 'CREATE TABLE users' in SQL_SCHEMA
        assert 'CREATE TABLE photos' in SQL_SCHEMA
        assert 'CREATE TABLE matches' in SQL_SCHEMA
        assert 'CREATE TABLE payments' in SQL_SCHEMA
        assert 'CREATE TABLE referrals' in SQL_SCHEMA
    
    @patch('src.database.supabase_client.supabase.db')
    def test_user_operations(self, mock_db):
        """Test user CRUD operations"""
        # Mock insert
        mock_db.return_value.insert.return_value.execute.return_value.data = [{'id': '123'}]
        
        # Test create user
        user = supabase.create_user(
            telegram_id=123456,
            full_name="Test User",
            age=25,
            gender='male'
        )
        
        assert user is not None
        
        # Mock select
        mock_db.return_value.select.return_value.eq.return_value.execute.return_value.data = [{'id': '123'}]
        
        # Test get user
        result = supabase.get_user(123456)
        assert result is not None

# Run tests with: pytest tests/ -v --cov=src