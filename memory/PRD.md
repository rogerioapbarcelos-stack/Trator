# TratorShop - Product Requirements Document

## Project Overview
**Name:** TratorShop  
**Type:** Agricultural Machinery Marketplace  
**Target Region:** Mato Grosso do Sul, Brazil  
**Last Updated:** 2026-03-21

## Original Problem Statement
Create a modern marketplace website called TratorShop - a classified marketplace for agricultural machinery. Connect buyers and sellers of tractors and agricultural equipment in Mato Grosso do Sul, Brazil.

## User Personas
1. **Seller (Farmer/Individual):** Lists machinery for sale with photos and specs, receives WhatsApp inquiries
2. **Dealer (Store):** Professional seller with store profile, multiple listings, branding
3. **Buyer (Farmer/Entrepreneur):** Searches for specific machinery types in specific cities, contacts sellers directly
4. **Admin:** Approves/rejects listings, manages featured ads, manages dealers

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

### Phase 3: Dealer System V1 (Complete - 2026-03-21)
- ✅ New user role: DEALER
- ✅ Dealer profile fields: store_name, store_slug, store_logo, whatsapp, city, description
- ✅ Dealer listing limits (admin configurable, default: 20)
- ✅ Public dealer page at /loja/{store-slug}
- ✅ Admin panel: Dealers tab
- ✅ Admin: Promote user to dealer
- ✅ Admin: Set listing limit per dealer
- ✅ Admin: Activate/deactivate dealer
- ✅ Admin: Demote dealer to regular user
- ✅ Dashboard: Dealer info card with stats
- ✅ Dashboard: Listing limit enforcement
- ✅ Header: "Minha Loja" link for dealers

## Tech Stack
- **Frontend:** React 19, TailwindCSS, Shadcn/UI, React Router v7, React-Leaflet
- **Backend:** FastAPI, Motor (MongoDB async)
- **Database:** MongoDB
- **Auth:** Emergent Google OAuth (users) + Email/Password (admins)
- **Storage:** Emergent Object Storage

## Admin Credentials
- Email: admin@tratorshop.com
- Password: Admin@123 (must change on first login)

## API Endpoints

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/ | API info |
| GET | /api/categories | List categories |
| GET | /api/cities | MS cities list |
| GET | /api/stats | Marketplace stats |
| GET | /api/listings | List approved listings |
| GET | /api/dealers/{slug} | Get dealer public profile |
| GET | /api/dealers/{slug}/listings | Get dealer's listings |

### Authenticated (User)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/listings | Create listing |
| PUT | /api/listings/{id} | Update listing |
| DELETE | /api/listings/{id} | Delete listing |
| GET | /api/my-listings | User's listings |
| GET | /api/dealer/profile | Dealer's own profile |
| PUT | /api/dealer/profile | Update dealer profile |
| POST | /api/dealer/logo | Upload dealer logo |

### Admin Only
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/listings | All listings |
| POST | /api/admin/listings/{id}/approve | Approve listing |
| POST | /api/admin/listings/{id}/reject | Reject listing |
| GET | /api/admin/dealers | List all dealers |
| POST | /api/admin/dealers/promote | Promote user to dealer |
| PUT | /api/admin/dealers/{id}/limit | Set dealer limit |
| POST | /api/admin/dealers/{id}/toggle-active | Toggle dealer status |
| DELETE | /api/admin/dealers/{id} | Demote dealer |

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Dealer profile editing page
- [ ] Dealer logo upload in dashboard
- [ ] Email notifications for approval/rejection

### P1 (High Priority)
- [ ] List all stores page (/lojas)
- [ ] Sitemap.xml generation
- [ ] Image compression/optimization
- [ ] Dealer plans (Basic/Premium)

### P2 (Medium Priority)
- [ ] User profile page
- [ ] Favorite/save listings
- [ ] Advanced filters (price range, year, hours)
- [ ] Share listing on social media

### P3 (Low Priority)
- [ ] Seller ratings/reviews
- [ ] SMS notifications (Twilio)
- [ ] Analytics dashboard for sellers

## Next Actions
1. Implement dealer profile editing in dashboard
2. Add dealer logo upload functionality
3. Create /lojas page listing all dealers
4. Implement email notifications for listing status
