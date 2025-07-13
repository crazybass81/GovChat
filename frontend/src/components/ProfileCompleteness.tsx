interface UserProfile {
  age?: number;
  region?: string;
  employment?: string;
  income?: string;
  maritalStatus?: string;
  education?: string;
  businessType?: string;
}

interface ProfileCompletenessProps {
  userProfile: UserProfile
}

const PROFILE_FIELDS = [
  'age', 'region', 'employment', 'income', 'maritalStatus', 'education', 'businessType'
] as const

export function ProfileCompleteness({ userProfile }: ProfileCompletenessProps) {
  const filledFields = PROFILE_FIELDS.filter(field => 
    userProfile[field] !== undefined && userProfile[field] !== null && userProfile[field] !== ''
  ).length
  
  const completionPercentage = Math.round((filledFields / PROFILE_FIELDS.length) * 100)

  return (
    <div className="bg-blue-50 p-3 border-b">
      <div className="flex items-center justify-between text-sm">
        <span className="text-blue-700">프로필 완성도</span>
        <span className="text-blue-600 font-medium">
          {completionPercentage}% ({filledFields}/{PROFILE_FIELDS.length})
        </span>
      </div>
      <div className="w-full bg-blue-200 rounded-full h-2 mt-1">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${completionPercentage}%` }}
          role="progressbar"
          aria-valuenow={completionPercentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`프로필 완성도 ${completionPercentage}%`}
        />
      </div>
    </div>
  )
}