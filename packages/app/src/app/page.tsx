import { Earth } from '@/components/earth'
import { StatCard } from '@/components/stat-card'
import { Ticker } from '@/components/ticker'
import { Badge } from '@/components/ui/badge'

export default function Home() {
  return (
    <section className='container mx-auto px-4 pt-16 pb-24'>
      <div className='flex flex-col items-center text-center mb-8'>
        <Badge className='mb-4 bg-cyan-900/30 text-cyan-400 border-cyan-500/50 tracking-widest'>PROTOCOL v1.0.3</Badge>
        <h1 className='text-5xl md:text-7xl font-bold tracking-wider mb-4 text-[#e4e942]'>VERIGREEN</h1>

        <p className='text-lg md:text-xl text-gray-400 max-w-2xl tracking-wide mb-8'>
          Blockchain-powered environmental verification protocol
        </p>

        {/* Ticker positioned under subtitle */}
        <div className='w-full max-w-4xl mb-8'>
          <Ticker />
        </div>
      </div>

      {/* Earth display */}
      <div className='relative flex justify-center my-12'>
        <Earth />
      </div>

      {/* Stats grid */}
      <div className='grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 mt-16 max-w-5xl mx-auto'>
        <StatCard title='REGIONS MAPPED' value='142' change='+3' icon='globe' />
        <StatCard title='FOREST TILES' value='1.2M' change='+24K' icon='trees' />
        <StatCard title='VERIFICATION RATE' value='99.2%' change='+0.3%' icon='check-circle' />
      </div>
    </section>
  )
}
