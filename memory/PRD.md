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

## What's Been Implemented (MVP - 2026-03-20)

### Backend (FastAPI + MongoDB)
- ✅ User authentication via Emergent Google OAuth
- ✅ Session management with cookies
- ✅ Listing CRUD operations
- ✅ Admin approval/rejection workflow
- ✅ Featured listings toggle
- ✅ 90-day auto-expiration check
- ✅ WhatsApp click tracking
- ✅ Object Storage integration for images
- ✅ MS cities endpoint
- ✅ Categories endpoint
- ✅ Marketplace stats

### Frontend (React)
- ✅ Homepage with hero, search, categories, featured/recent listings
- ✅ Search page with filters (category, city, text)
- ✅ Listing detail page with specs, images, WhatsApp button
- ✅ User dashboard (manage listings)
- ✅ Admin panel (approve/reject/feature)
- ✅ Create listing form
- ✅ Google OAuth login flow
- ✅ Mobile responsive design
- ✅ Outfit + Inter typography
- ✅ Green (#1A4D2E) + Gold (#F9C02D) color palette

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Shadcn/UI, React Router v7
- **Backend:** FastAPI, Motor (MongoDB async)
- **Database:** MongoDB
- **Auth:** Emergent Google OAuth
- **Storage:** Emergent Object Storage
- **Maps:** OpenStreetMap/Leaflet (ready for integration)

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Image upload UI on create listing form
- [ ] Edit listing functionality
- [ ] Email notifications for approval/rejection

### P1 (High Priority)
- [ ] Leaflet map integration on listing detail
- [ ] SEO meta tags per page
- [ ] Sitemap generation
- [ ] Listing expiration notifications

### P2 (Medium Priority)
- [ ] User profile page
- [ ] Favorite/save listings
- [ ] Listing renewal option
- [ ] Advanced filters (price range, year, hours)
- [ ] Share listing on social media

### P3 (Low Priority)
- [ ] Seller ratings/reviews
- [ ] Multiple image gallery with drag-drop reorder
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

## Next Actions
1. Implement image upload UI in create listing form
2. Add edit listing functionality
3. Integrate Leaflet map on listing detail page
4. Add SEO meta tags
5. Create admin notification system
