'use client'

import React from 'react'
import Image from 'next/image'
import { LinkComponent } from './LinkComponent'
import { SITE_EMOJI } from '@/utils/site'
import { Connect } from './Connect'
import { NotificationsDrawer } from './NotificationsDrawer'
import { useAccount } from 'wagmi'
import verigreenLogo from '@/assets/icons/verigreen_logo.png'

export function Header() {
  const { isConnected } = useAccount()

  return (
    <header className='sticky top-0 z-50 w-full border-b border-gray-200 bg-white/80 backdrop-blur-sm dark:border-gray-800 dark:bg-gray-950/80'>
      <div className='container mx-auto flex h-20 items-center justify-between px-4'>
        <LinkComponent href='/'>
          <div className='relative h-16 w-48 hover:opacity-80 transition-opacity'>
            <Image src={verigreenLogo} alt='VeriGreen Logo' fill className='object-contain object-left' priority />
          </div>
        </LinkComponent>

        <div className='flex items-center gap-4'>
          {isConnected && (
            <LinkComponent href='/dashboard'>
              <button className='inline-flex items-center justify-center rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-green-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-950'>
                Land Owner
              </button>
            </LinkComponent>
          )}
          <div className='flex items-center gap-2'>
            <Connect />
            <NotificationsDrawer />
          </div>
        </div>
      </div>
    </header>
  )
}
