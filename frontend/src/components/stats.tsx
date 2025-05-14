'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { useState, useEffect } from 'react'

interface Stat {
  value: number
  label: string
  prefix?: string
  suffix?: string
}

interface StatsProps {
  stats: Stat[]
}

export function Stats({ stats }: StatsProps) {
  const { ref, inView } = useInView({
    threshold: 0.3,
    triggerOnce: true
  })

  return (
    <div ref={ref} className="grid grid-cols-2 lg:grid-cols-4 gap-8">
      {stats.map((stat, index) => (
        <StatCard key={index} stat={stat} animate={inView} delay={index * 0.2} />
      ))}
    </div>
  )
}

function StatCard({ stat, animate, delay }: { stat: Stat; animate: boolean; delay: number }) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    if (animate) {
      const duration = 2000 // Animation duration in milliseconds
      const steps = 60 // Number of steps in the animation
      const stepValue = stat.value / steps
      const stepDuration = duration / steps

      let currentStep = 0
      const timer = setInterval(() => {
        if (currentStep < steps) {
          setDisplayValue(Math.round(stepValue * (currentStep + 1)))
          currentStep++
        } else {
          clearInterval(timer)
        }
      }, stepDuration)

      return () => clearInterval(timer)
    }
  }, [animate, stat.value])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: animate ? 1 : 0, y: animate ? 0 : 20 }}
      transition={{ duration: 0.6, delay }}
      className="text-center p-6 rounded-lg bg-card border border-border"
    >
      <motion.div
        initial={{ scale: 0.5 }}
        animate={{ scale: animate ? 1 : 0.5 }}
        transition={{ type: "spring", stiffness: 100, delay: delay + 0.2 }}
        className="text-4xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400"
      >
        {stat.prefix}{displayValue.toLocaleString()}{stat.suffix}
      </motion.div>
      <div className="text-muted-foreground">{stat.label}</div>
    </motion.div>
  )
} 