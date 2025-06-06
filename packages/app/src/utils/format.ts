import { formatEther } from 'viem'

export function TruncateMiddle(text: string, length: number = 5) {
  if (text?.length > length * 2 + 1) {
    return `${text.substring(0, length)}...${text.substring(text.length - length, text.length)}`
  }

  return text
}

export function formatBalance(balance: bigint, toFixed?: number) {
  return parseFloat(formatEther(balance, 'wei')).toFixed(toFixed ?? 4)
}
