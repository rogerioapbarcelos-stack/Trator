# TratorShop - Product Requirements Document

## Project Overview
**Name:** TratorShop  
**Type:** Agricultural Machinery Marketplace  
**Target Region:** Mato Grosso do Sul, Brazil  
**Last Updated:** 2026-03-20

## Original Problem Statement
Create a modern marketplace website called TratorShop - a classified marketplace for agricultural machinery (NOT an online store). Goal: Connect buyers and sellers of tractors and agricultural equipment in Mato Grosso do Sul, Brazil.

## User Personas
1. **Seller (Farmer/Dealer):** Wants to list machinery for sale with photos and specs, receive WhatsApp inquiries
2. **Buyer (Farmer/Entrepreneur):** Searches for specific machinery types in specific cities, contacts sellers directly
3. **Admin:** Approves/rejects listings, manages featured ads

## Core Requirements (Static)
- Search by machine type and city
- Category browsing (Tratores, Implementos, Colheitadeiras, Peças)
- Listing with images, specs, WhatsApp contact
- User authentication via Google OAuth
- Admin approval workflow before publishing
- 90-day automatic ad expiration
- Featured listings system
- WhatsApp click tracking
- Mobile-first, SEO optimized

## What's Been Implemented

### Phase 1: MVP (2026-03-20)
- ✅ User authentication via Emergent Google OAuth
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
- ✅ Mobile responsive design

### Phase 2: MVP Optimization (2026-03-20)
- ✅ **Image Upload UI** - Integrated image uploader in create/edit listing forms
- ✅ **Edit Listing** - Full edit functionality with existing data preloaded
- ✅ **Leaflet Maps** - Interactive OpenStreetMap on listing detail pages
- ✅ **SEO Meta Tags** - Dynamic meta tags for all pages (title, description, og:*, twitter:*)
- ✅ **Base HTML SEO** - Server-rendered meta tags for crawlers
- ✅ **SEOHead Component** - Reusable component for page-specific meta tags

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Shadcn/UI, React Router v7, React-Leaflet
- **Backend:** FastAPI, Motor (MongoDB async)
- **Database:** MongoDB
- **Auth:** Emergent Google OAuth
- **Storage:** Emergent Object Storage
- **Maps:** OpenStreetMap via Leaflet

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Email notifications for approval/rejection
- [ ] Image reordering (drag-drop)
- [ ] Listing renewal before expiration

### P1 (High Priority)
- [ ] Sitemap.xml generation
- [ ] robots.txt optimization
- [ ] Image compression/optimization
- [ ] Lazy loading for images

### P2 (Medium Priority)
- [ ] User profile page
- [ ] Favorite/save listings
- [ ] Advanced filters (price range, year, hours)
- [ ] Share listing on social media

### P3 (Low Priority)
- [ ] Seller ratings/reviews
- [ ] SMS notifications (Twilio)
- [ ] Analytics dashboard for sellers

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/ | No | API info |
| GET | /api/categories | No | List categories |
| GET | /api/cities | No | MS cities list |
| GET | /api/stats | No | Marketplace stats |
| GET | /api/listings | No | List approved listings |
| GET | /api/listings/featured | No | Featured listings |
| GET | /api/listings/{id} | No | Single listing |
| POST | /api/listings | Yes | Create listing |
| PUT | /api/listings/{id} | Yes | Update listing |
| DELETE | /api/listings/{id} | Yes | Delete listing |
| POST | /api/listings/{id}/images | Yes | Upload image |
| POST | /api/listings/{id}/whatsapp-click | No | Track click |
| GET | /api/my-listings | Yes | User's listings |
| POST | /api/auth/session | No | Exchange session |
| GET | /api/auth/me | Yes | Current user |
| POST | /api/auth/logout | Yes | Logout |
| GET | /api/admin/listings | Admin | All listings |
| POST | /api/admin/listings/{id}/approve | Admin | Approve |
| POST | /api/admin/listings/{id}/reject | Admin | Reject |
| POST | /api/admin/listings/{id}/feature | Admin | Toggle featured |

## SEO Implementation
- Base meta tags in index.html (for crawlers)
- Dynamic meta tags via SEOHead component
- Per-listing SEO with title, price, location, image
- Search page SEO based on filters
- Clean URL structure (/anuncio/{id}, /buscar, /dashboard)

## Next Actions
1. Implement email notifications for listing status changes
2. Add image reordering functionality
3. Generate sitemap.xml for better SEO
4. Optimize images with compression
