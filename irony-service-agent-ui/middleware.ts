import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  // Check for the presence of the 'auth_token' cookie
  console.log("Request cookies: ", req.cookies);
  //   const token = req.cookies.get("auth_token");

  //   // Redirect to login if the cookie is not present (likely expired)
  //   if (!token) {
  //     return NextResponse.redirect(new URL("/login", req.url));
  //   }

  // Allow the request to proceed if the cookie is present
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"], // Define protected routes
};
