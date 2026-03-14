-- Run this in Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    
    -- Profile
    full_name TEXT,
    age INT CHECK (age >= 18 AND age <= 100),
    gender TEXT CHECK (gender IN ('male', 'female')),
    location TEXT,
    region TEXT,
    country TEXT DEFAULT 'Ethiopia',
    
    -- Habesha specific
    ethnicity TEXT,
    religion TEXT,
    church TEXT,
    occupation TEXT,
    education TEXT,
    bio TEXT,
    
    -- Preferences
    looking_for TEXT DEFAULT 'female',
    
    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'rejected', 'suspended', 'expired')),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by BIGINT,
    
    -- Subscription
    subscription_active BOOLEAN DEFAULT FALSE,
    subscription_start TIMESTAMPTZ,
    subscription_end TIMESTAMPTZ,
    payment_status TEXT DEFAULT 'pending',
    
    -- Matching
    weekly_likes INT DEFAULT 5,
    likes_reset_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Referral
    referral_code TEXT UNIQUE,
    referred_by UUID REFERENCES users(id),
    total_referrals INT DEFAULT 0,
    paid_referrals INT DEFAULT 0,
    
    -- Language
    language TEXT DEFAULT 'en',
    
    -- Settings
    show_location BOOLEAN DEFAULT TRUE,
    show_age BOOLEAN DEFAULT TRUE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Photos table
CREATE TABLE photos (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    thumbnail_url TEXT,
    is_selfie BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by BIGINT,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Matches table
CREATE TABLE matches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
    match_type TEXT DEFAULT 'like',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    matched_at TIMESTAMPTZ,
    UNIQUE(user1_id, user2_id)
);

-- Likes table
CREATE TABLE likes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    to_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    like_type TEXT DEFAULT 'like',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(from_user_id, to_user_id)
);

-- Blocks table
CREATE TABLE blocks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    blocked_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, blocked_user_id)
);

-- Payments table
CREATE TABLE payments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    duration_days INT DEFAULT 90,
    receipt_url TEXT,
    status TEXT DEFAULT 'pending',
    admin_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    processed_by BIGINT,
    metadata JSONB DEFAULT '{}'
);

-- Referrals table
CREATE TABLE referrals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    referrer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    referred_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    referral_code TEXT,
    status TEXT DEFAULT 'registered',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ,
    subscription_granted_at TIMESTAMPTZ
);

-- Announcements table
CREATE TABLE announcements (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    target TEXT DEFAULT 'all',
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT,
    sent_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ
);

-- Activity log for analytics
CREATE TABLE activity_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_gender ON users(gender);
CREATE INDEX idx_users_location ON users(location);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_photos_user_id ON photos(user_id);
CREATE INDEX idx_matches_users ON matches(user1_id, user2_id);
CREATE INDEX idx_likes_from_user ON likes(from_user_id);
CREATE INDEX idx_likes_to_user ON likes(to_user_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_activity_user ON activity_log(user_id);
CREATE INDEX idx_activity_created ON activity_log(created_at);

-- Create RPC function for potential matches
CREATE OR REPLACE FUNCTION get_potential_matches(
    p_user_id UUID,
    p_gender TEXT,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    full_name TEXT,
    age INT,
    location TEXT,
    region TEXT,
    religion TEXT,
    occupation TEXT,
    bio TEXT,
    profile_photos JSON,
    compatibility_score FLOAT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.full_name,
        u.age,
        u.location,
        u.region,
        u.religion,
        u.occupation,
        u.bio,
        (
            SELECT json_agg(json_build_object('url', p.photo_url, 'thumbnail', p.thumbnail_url))
            FROM photos p
            WHERE p.user_id = u.id AND p.is_approved = TRUE
            LIMIT 5
        ) as profile_photos,
        -- Simple compatibility score (can be enhanced)
        CASE 
            WHEN u.religion = (SELECT religion FROM users WHERE id = p_user_id) THEN 0.3
            ELSE 0
        END +
        CASE 
            WHEN u.region = (SELECT region FROM users WHERE id = p_user_id) THEN 0.2
            ELSE 0
        END as compatibility_score
    FROM users u
    WHERE 
        u.id != p_user_id
        AND u.gender = p_gender
        AND u.status = 'active'
        AND u.subscription_active = TRUE
        AND NOT EXISTS (
            SELECT 1 FROM blocks b 
            WHERE (b.user_id = p_user_id AND b.blocked_user_id = u.id)
               OR (b.user_id = u.id AND b.blocked_user_id = p_user_id)
        )
        AND NOT EXISTS (
            SELECT 1 FROM likes l 
            WHERE l.from_user_id = p_user_id AND l.to_user_id = u.id
        )
    ORDER BY compatibility_score DESC, u.created_at DESC
    LIMIT p_limit;
END;
$$;