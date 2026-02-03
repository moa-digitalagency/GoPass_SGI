// Extracted from finance/deposits.html

function openDepositModal(id, name, balance) {
        document.getElementById('depositModal').classList.remove('hidden');
        document.getElementById('agent_id').value = id;
        document.getElementById('agent_name').value = name;
        document.getElementById('amount').value = balance > 0 ? balance.toFixed(2) : '';
    }

    function closeDepositModal() {
        document.getElementById('depositModal').classList.add('hidden');
    }