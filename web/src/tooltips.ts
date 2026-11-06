// 머리글 툴팁 문구(IMP-1, IMP-2). id는 aria-describedby가 가리킨다.
export const HEADER_TIPS = {
  setNo: {
    id: 'tip-set-no',
    text: '지금까지 시작한 세트의 순번이다. 복습 문제가 다시 나오는 시점을 이 번호로 센다.',
  },
  audit: {
    id: 'tip-audit',
    text: '고정한 문제 풀에서 무작위로 뽑은 20문항을 직접 검토하고 오류를 표시하는 화면이다.',
  },
} as const
