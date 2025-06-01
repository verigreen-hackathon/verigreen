import { prisma } from '../config/prisma'

export class SubmissionService {
  async getSubmissionsByOwner(owner: string) {
    return await prisma.submission.findMany({
      where: {
        user_address: {
          contains: owner,
          mode: 'insensitive',
        },
      },
      include: {
        verifierResponse: true,
      },
    })
  }
}
