'use client'

import Image from 'next/image'
import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'

export function HeroImage() {
  return (
    <div className="relative w-full h-[500px] lg:h-[600px]">
      {/* Background glow effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-primary/20 to-purple-500/20 rounded-2xl blur-3xl"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1 }}
      />

      {/* Bot icon with waves */}
      <div className="absolute top-8 right-4 z-10">
        <motion.div
          className="relative"
          animate={{ y: [0, -8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className="relative">
            {/* Animated waves */}
            {[...Array(3)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute inset-0 rounded-full bg-primary/20"
                initial={{ scale: 1, opacity: 0.5 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.4,
                  ease: "easeOut"
                }}
              />
            ))}
            {/* Bot icon container */}
            <div className="relative w-14 h-14 rounded-full bg-primary flex items-center justify-center shadow-lg">
              <Bot className="w-7 h-7 text-primary-foreground" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Main image */}
      <motion.div
        className="relative w-full h-full"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <Image
          src="/d1.png"
          alt="ChatSphere Dashboard"
          fill
          className="object-contain rounded-xl"
          priority
        />
      </motion.div>

      {/* Floating elements */}
      <motion.div
        className="absolute -top-12 right-12 w-32 h-32 bg-primary/10 rounded-full blur-xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0.8, 0.5],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute -bottom-8 -left-8 w-40 h-40 bg-purple-500/10 rounded-full blur-xl"
        animate={{
          scale: [1, 1.3, 1],
          opacity: [0.5, 0.8, 0.5],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1
        }}
      />
    </div>
  )
} 