/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: '**.images-na.ssl-images-amazon.com',
      },
      {
        protocol: 'https',
        hostname: '**.m.media-amazon.com',
      },
      {
        protocol: 'https',
        hostname: '**.slickdeals.net',
      },
      {
        protocol: 'https',
        hostname: '**.dealmoon.com',
      },
      {
        protocol: 'https',
        hostname: '**.coupons.com',
      },
      {
        protocol: 'https',
        hostname: '**.retailmenot.com',
      },
      {
        protocol: 'https',
        hostname: '**.yimg.com',
      },
      {
        protocol: 'https',
        hostname: '**.gstatic.com',
      },
      {
        protocol: 'https',
        hostname: '**.googleusercontent.com',
      },
      {
        protocol: 'https',
        hostname: '**.burgerking.com',
      },
      {
        protocol: 'https',
        hostname: '**.mcdonalds.com',
      },
      {
        protocol: 'https',
        hostname: '**.subway.com',
      },
      {
        protocol: 'https',
        hostname: '**.tacobell.com',
      },
      {
        protocol: 'https',
        hostname: '**.dominos.com',
      },
      {
        protocol: 'https',
        hostname: '**.chipotle.com',
      },
    ],
  },
}

module.exports = nextConfig

