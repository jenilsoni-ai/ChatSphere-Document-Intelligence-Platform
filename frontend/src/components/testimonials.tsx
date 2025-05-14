'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import Image from 'next/image'
import { Quote } from 'lucide-react'

interface Testimonial {
  quote: string
  author: string
  role: string
  company: string
  image: string
}

interface TestimonialsProps {
  testimonials: Testimonial[]
}

export function Testimonials({ testimonials }: TestimonialsProps) {
  const { ref, inView } = useInView({
    threshold: 0.1,
    triggerOnce: true
  })

  return (
    <div ref={ref} className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
      {testimonials.map((testimonial, index) => (
        <TestimonialCard
          key={index}
          testimonial={testimonial}
          animate={inView}
          delay={index * 0.2}
        />
      ))}
    </div>
  )
}

function TestimonialCard({
  testimonial,
  animate,
  delay
}: {
  testimonial: Testimonial
  animate: boolean
  delay: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: animate ? 1 : 0, y: animate ? 0 : 20 }}
      transition={{ duration: 0.6, delay }}
      className="relative p-6 rounded-lg bg-card border border-border group hover:shadow-lg transition-shadow"
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-purple-400/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Quote icon */}
      <div className="relative">
        <Quote className="w-10 h-10 text-primary/20 mb-4" />
        <blockquote className="text-lg mb-6">{testimonial.quote}</blockquote>
        
        {/* Author info */}
        <div className="flex items-center gap-4">
          <div className="relative w-12 h-12 rounded-full overflow-hidden border-2 border-border">
            <Image
              src={testimonial.image}
              alt={testimonial.author}
              fill
              className="object-cover"
            />
          </div>
          <div>
            <div className="font-semibold">{testimonial.author}</div>
            <div className="text-sm text-muted-foreground">
              {testimonial.role} at {testimonial.company}
            </div>
          </div>
        </div>
      </div>

      {/* Decorative elements */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: animate ? 1 : 0 }}
        transition={{ type: "spring", stiffness: 100, delay: delay + 0.3 }}
        className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-primary"
      />
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: animate ? 1 : 0 }}
        transition={{ type: "spring", stiffness: 100, delay: delay + 0.4 }}
        className="absolute -bottom-2 -left-2 w-4 h-4 rounded-full bg-purple-400"
      />
    </motion.div>
  )
} 