import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight, Bot, Zap, Shield, MessageSquare, Code, Sparkles } from 'lucide-react'
import { HeroImage } from '@/components/hero-image'
import { Stats } from '@/components/stats'
import { Testimonials } from '@/components/testimonials'

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
            ChatSphere
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="container py-24">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            {/* Left column - Text content */}
            <div className="flex-1 text-center lg:text-left space-y-8 lg:pl-8">
              <h1 className="text-4xl lg:text-6xl font-bold">
                Build AI Chatbots with{' '}
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                  ChatSphere
                </span>
              </h1>
              <p className="text-xl text-muted-foreground max-w-xl">
                Create, train, and deploy intelligent chatbots that understand your business.
                Enhance customer support and automate conversations with ease.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Button size="lg" asChild>
                  <Link href="/register">Start Building</Link>
                </Button>
              </div>
            </div>

            {/* Right column - Hero image */}
            <div className="flex-1 w-full max-w-2xl lg:-translate-x-4">
              <HeroImage />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Everything You Need to Build Better Chatbots</h2>
            <p className="text-xl text-muted-foreground">
              Powerful features that make ChatSphere the perfect choice for your business
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="p-6 rounded-lg border border-border bg-card hover:shadow-lg transition-shadow"
              >
                <feature.icon className="w-12 h-12 text-primary mb-4" />
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="container py-12 border-t">
        <div className="text-center space-y-4 mb-8">
          <h2 className="text-2xl font-medium text-muted-foreground">
            Trusted by innovative teams worldwide
          </h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center justify-items-center opacity-75">
          <div className="w-32 h-12 bg-muted rounded-md animate-pulse" />
          <div className="w-32 h-12 bg-muted rounded-md animate-pulse" />
          <div className="w-32 h-12 bg-muted rounded-md animate-pulse" />
          <div className="w-32 h-12 bg-muted rounded-md animate-pulse" />
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="container py-24 space-y-8">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-bold">Trusted by Industry Leaders</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            See what our customers have to say about their experience with ChatSphere
          </p>
        </div>
        <Testimonials testimonials={testimonials} />
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Customer Support?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of businesses using ChatSphere to deliver exceptional customer experiences.
          </p>
          <Link href="/register">
            <Button size="lg" variant="secondary" className="gap-2">
              Get Started Now <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-border">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <Link href="/" className="text-xl font-bold mb-4 block">
                ChatSphere
              </Link>
              <p className="text-sm text-muted-foreground">
                Building the future of customer interactions with AI.
              </p>
            </div>
            {footerLinks.map((section, index) => (
              <div key={index}>
                <h4 className="font-semibold mb-4">{section.title}</h4>
                <ul className="space-y-2">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <Link href={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="mt-12 pt-8 border-t border-border text-center text-sm text-muted-foreground">
            © {new Date().getFullYear()} ChatSphere. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}

const features = [
  {
    icon: Bot,
    title: 'Advanced AI Understanding',
    description: 'Powered by state-of-the-art language models for human-like conversations and accurate responses.'
  },
  {
    icon: MessageSquare,
    title: 'Multi-Channel Support',
    description: 'Deploy your chatbot across Slack, Discord, your website, and more with seamless integration.'
  },
  {
    icon: Code,
    title: 'Easy Integration',
    description: 'Simple API and SDK options to add ChatSphere to your existing applications in minutes.'
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Bank-grade encryption and compliance features to keep your data safe and secure.'
  },
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Optimized performance with response times under 100ms for real-time conversations.'
  },
  {
    icon: Sparkles,
    title: 'Custom Training',
    description: 'Train your bot with your own data and documents for personalized responses.'
  }
]

const footerLinks = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '/features' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Security', href: '/security' },
      { label: 'Enterprise', href: '/enterprise' }
    ]
  },
  {
    title: 'Resources',
    links: [
      { label: 'Documentation', href: '/docs' },
      { label: 'API Reference', href: '/api' },
      { label: 'Guides', href: '/guides' },
      { label: 'Blog', href: '/blog' }
    ]
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '/about' },
      { label: 'Careers', href: '/careers' },
      { label: 'Contact', href: '/contact' },
      { label: 'Legal', href: '/legal' }
    ]
  }
]

const testimonials = [
  {
    quote: "ChatSphere has transformed how we handle customer support. The AI's understanding of context is remarkable, and the integration was seamless.",
    author: "Sarah Chen",
    role: "Head of Customer Success",
    company: "TechFlow Inc",
    image: "/testimonials/sarah.jpg"
  },
  {
    quote: "We've seen a 60% reduction in response time and improved customer satisfaction since implementing ChatSphere. It's been a game-changer.",
    author: "Michael Rodriguez",
    role: "CTO",
    company: "DataSync Solutions",
    image: "/testimonials/michael.jpg"
  },
  {
    quote: "The multi-channel support and custom training capabilities make ChatSphere stand out. It's like having a dedicated support team that never sleeps.",
    author: "Emma Thompson",
    role: "Operations Director",
    company: "GlobalTech",
    image: "/testimonials/emma.jpg"
  }
]
