# TratorShop - Product Requirements Document

## Project Overview
**Name:** TratorShop  
**Type:** Agricultural Machinery Marketplace  
**Target Region:** Mato Grosso do Sul, Brazil  
**Last Updated:** 2026-03-21

## Original Problem Statement
Continue existing project TratorShop from GitHub - a marketplace platform with admin panel and authentication system for agricultural machinery (tractors, implements, harvesters, parts).

## User Personas
1. **Seller (Farmer/Dealer):** Lists machinery for sale with photos and specs, receives WhatsApp inquiries
2. **Buyer (Farmer/Entrepreneur):** Searches for specific machinery types in specific cities, contacts sellers directly
3. **Admin:** Approves/rejects listings, manages featured ads, user management

## Core Requirements (Static)
- Search by machine type and city
- Category browsing (Tratores, Implementos, Colheitadeiras, Peças)
- Listing with images, specs, WhatsApp contact
- User authentication via Google OAuth
- Separate Admin authentication with email/password
- Admin approval workflow before publishing
- 90-day automatic ad expiration
- Featured listings system
- WhatsApp click tracking
- Mobile-first, SEO optimized

## What's Been Implemented

### Phase 1: MVP (Complete)
- ✅ User authentication via Emergent Google OAuth
- ✅ Admin authentication system (email/password)
- ✅ Session management with cookies
- ✅ Listing CRUD operations
- ✅ Admin approval/rejection workflow
- ✅ Featured listings toggle
- ✅ 90-day auto-expiration check
- ✅ WhatsApp click tracking
- ✅ Object Storage integration for images
- ✅ Homepage with hero, search, categories, featured/recent listings
- ✅ Search page with filters
- ✅ Listing detail page
- ✅ User dashboard
- ✅ Admin panel

### Phase 2: MVP Optimization (Complete)
- ✅ Image Upload UI
- ✅ Edit Listing functionality
- ✅ Leaflet Maps integration
- ✅ SEO Meta Tags
- ✅ Mobile responsive design

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Shadcn/UI, React Router v7, React-Leaflet
- **Backend:** FastAPI, Motor (MongoDB async)
- **Database:** MongoDB
- **Auth:** Emergent Google OAuth (users) + Email/Password (admins)
- **Storage:** Emergent Object Storage

## Admin Credentials
- Email: admin@tratorshop.com
- Password: Admin@123 (must change on first login)

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Email notifications for approval/rejection
- [ ] Image reordering (drag-drop)
- [ ] Listing renewal before expiration

### P1 (High Priority)
- [ ] Sitemap.xml generation
- [ ] robots.txt optimization
- [ ] Image compression/optimization

### P2 (Medium Priority)
- [ ] User profile page
- [ ] Favorite/save listings
- [ ] Advanced filters (price range, year, hours)

## API Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/ | No | API info |
| GET | /api/categories | No | List categories |
| GET | /api/cities | No | MS cities list |
| GET | /api/stats | No | Marketplace stats |
| GET | /api/listings | No | List approved listings |
| POST | /api/listings | User | Create listing |
| PUT | /api/listings/{id} | Owner | Update listing |
| DELETE | /api/listings/{id} | Owner/Admin | Delete listing |
| POST | /api/auth/session | No | Exchange session |
| POST | /api/admin/auth/login | No | Admin login |
| GET | /api/admin/listings | Admin | All listings |
| POST | /api/admin/listings/{id}/approve | Admin | Approve listing |
| POST | /api/admin/listings/{id}/reject | Admin | Reject listing |

## Next Actions
1. Implement email notifications for listing status changes
2. Add image reordering functionality
3. Generate sitemap.xml for better SEO
