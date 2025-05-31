import {
  Globe,
  Trees,
  ShieldCheck,
  Leaf,
  CheckCircle,
  Landmark,
  TrendingUp,
  TrendingDown,
  type LucideIcon,
} from "lucide-react"

interface StatCardProps {
  title: string
  value: string
  change: string
  icon: string
}

export function StatCard({ title, value, change, icon }: StatCardProps) {
  const isPositive = change.startsWith("+")

  const getIcon = (iconName: string): LucideIcon => {
    switch (iconName) {
      case "globe":
        return Globe
      case "trees":
        return Trees
      case "shield-check":
        return ShieldCheck
      case "leaf":
        return Leaf
      case "check-circle":
        return CheckCircle
      case "landmark":
        return Landmark
      default:
        return Globe
    }
  }

  const Icon = getIcon(icon)

  return (
    <div className="bg-black/40 backdrop-blur-sm border border-cyan-900/30 rounded-md p-4 hover:border-cyan-500/50 transition-colors group">
      <div className="flex justify-between items-start mb-3">
        <p className="text-xs text-gray-400 tracking-wider">{title}</p>
        <div className="size-8 rounded-md bg-cyan-900/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-900/30 transition-colors">
          <Icon className="size-4" />
        </div>
      </div>
      <p className="text-2xl font-bold text-white mb-1">{value}</p>
      <div className={`flex items-center text-xs ${isPositive ? "text-green-400" : "text-red-400"}`}>
        {isPositive ? <TrendingUp className="size-3 mr-1" /> : <TrendingDown className="size-3 mr-1" />}
        <span>{change}</span>
      </div>
    </div>
  )
}
