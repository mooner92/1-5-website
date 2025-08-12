document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    today.setHours(0,0,0,0);
    
    // 상태 및 날짜별로 카드 정렬
    const cardList = document.querySelector('.card-list.grid');
    if (cardList) {
        
        const cards = Array.from(cardList.children);
        cards.forEach(card => {
            const el = card.querySelector('.date[data-deadline]');
            const deadlineStr = el.getAttribute('data-deadline');
            const deadline = new Date(deadlineStr + "T23:59:59");
            deadline.setHours(23,59,59,999);
            const diffTime = deadline - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            card.dataset.deadline = deadlineStr;
            if (diffDays <= 0) {
                card.dataset.status = 'done';
            } else if (diffDays <= 2) {
                card.dataset.status = 'urgent';
            } else {
                card.dataset.status = 'scheduled';
            }
        });

        cards.sort((a, b) => {
            // urgent(빨강) < scheduled(파랑) < done(초록)
            const statusOrder = { urgent: 0, scheduled: 1, done: 2 };
            const aStatus = a.dataset.status;
            const bStatus = b.dataset.status;
            if (statusOrder[aStatus] !== statusOrder[bStatus]) {
                return statusOrder[aStatus] - statusOrder[bStatus];
            }
            // 같은 상태면 날짜 오름차순
            const aDate = new Date(a.dataset.deadline);
            const bDate = new Date(b.dataset.deadline);
            return aDate - bDate;
        });
        cards.forEach(card => cardList.appendChild(card));
    }

    // 상태별 스타일 적용
    document.querySelectorAll('.card .date[data-deadline]').forEach(function(el) {
        const deadlineStr = el.getAttribute('data-deadline');
        const deadline = new Date(deadlineStr + "T23:59:59");
        deadline.setHours(23,59,59,999);

        const diffTime = deadline - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const card = el.closest('.card');

        if (diffDays <= 0) {
            el.style.color = '#22c55e'; // 초록
            el.style.fontWeight = 'bold';
            if (!el.textContent.includes('완료')) {
                el.textContent += ' (완료)';
            }
            card.classList.add('done');
        } else if (diffDays <= 2) {
            el.style.color = '#ef4444'; // 빨강
            el.style.fontWeight = 'bold';
            card.classList.add('urgent');
        } else {
            card.classList.add('scheduled');
        }
    });
});