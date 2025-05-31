import { Shield, Leaf, Clock } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

interface RegionPanelProps {
  region: {
    id: string
    name: string
    greenCoverage: number
    verifiedArea: string
    validators: number
    lastVerification: string
  }
}

export function RegionPanel({ region }: RegionPanelProps) {
  return (
    <div className="h-full w-full bg-black/40 backdrop-blur-md border border-cyan-500/30 p-4 flex flex-col">
      <div className="mb-4 pb-3 border-b border-cyan-900/50">
        <h3 className="text-xl font-bold tracking-wider text-white">{region.name}</h3>
        <Badge className="mt-1 bg-green-900/30 text-green-400 border-green-500/50">VERIFIED</Badge>
      </div>

      <div className="space-y-6 flex-1">
        {/* Green coverage */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-xs text-gray-400 tracking-wider">GREEN COVERAGE</span>
            <span className="text-xs font-bold text-cyan-400">{region.greenCoverage}%</span>
          </div>
          <Progress value={region.greenCoverage} className="h-2 bg-gray-800" />
          <div className="mt-1 flex justify-between">
            <span className="text-[10px] text-gray-500">GLOBAL AVG: 32.4%</span>
            <span className="text-[10px] text-green-400">+2.1% YOY</span>
          </div>
        </div>

        {/* Verified area */}
        <div className="flex items-center gap-3">
          <div className="size-10 rounded-md bg-green-900/20 border border-green-500/30 flex items-center justify-center text-green-400">
            <Leaf className="size-5" />
          </div>
          <div>
            <p className="text-xs text-gray-400 tracking-wider">VERIFIED FOREST AREA</p>
            <p className="text-lg font-bold text-white">
              {region.verifiedArea} <span className="text-xs text-gray-400">hectares</span>
            </p>
          </div>
        </div>

        {/* Last verification */}
        <div className="flex items-center gap-3">
          <div className="size-10 rounded-md bg-gray-800/50 border border-gray-700 flex items-center justify-center text-gray-400">
            <Clock className="size-5" />
          </div>
          <div>
            <p className="text-xs text-gray-400 tracking-wider">LAST VERIFICATION</p>
            <p className="text-lg font-bold text-white">{region.lastVerification}</p>
          </div>
        </div>
      </div>

      {/* Blockchain verification */}
      <div className="mt-4 pt-3 border-t border-cyan-900/50">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">BLOCKCHAIN VERIFIED</span>
          <Badge className="bg-cyan-900/30 text-cyan-400 border-cyan-500/50 text-[10px]">0x71...3F4a</Badge>
        </div>
      </div>
    </div>
  )
}
