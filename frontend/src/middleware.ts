import { NextResponse } from 'next/server'

export function middleware(request: Request) {
  return NextResponse.next()
}

// Remove all route protection for now
export const config = {
  matcher: []
} 