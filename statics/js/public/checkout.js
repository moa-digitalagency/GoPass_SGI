/**
 * GoPass SGI-GP Checkout Logic
 * Extracted from templates/public/checkout.html
 */

let checkoutConfig = {};
let pricingOptions = {};
let currentCurrency = 'USD';
let unitPrice = 0;
let passengerCount = 1;
let stripe = null;
let elements = null;
let card = null;
let stripeEnabled = false;

function initCheckout(config) {
    checkoutConfig = config;
    pricingOptions = config.pricingOptions;
    unitPrice = pricingOptions[currentCurrency];

    const isDemoMode = config.isDemoMode;

    // DOM Elements
    const els = {
        step2Indicator: document.getElementById('step-2-indicator'),
        step3Indicator: document.getElementById('step-3-indicator'),
        mobileStepNum: document.getElementById('mobile-step-num'),
        mobileStepName: document.getElementById('mobile-step-name'),
        identitySection: document.getElementById('identity-section'),
        paymentSection: document.getElementById('payment-section'),
        btnContinue: document.getElementById('btn-continue'),
        btnAddPassenger: document.getElementById('btn-add-passenger'),
        passengersContainer: document.getElementById('passengers-container'),
        form: document.getElementById('checkout-form'),
        currencySelector: document.getElementById('currency-selector'),
        formCurrencyInput: document.getElementById('form-currency')
    };

    // --- PRICING LOGIC ---
    function updatePrice() {
        const total = passengerCount * unitPrice;

        const formatPrice = (val) => {
            return val.toLocaleString('fr-FR', { style: 'currency', currency: currentCurrency });
        };

        document.querySelectorAll('.total-price-display').forEach(el => {
            el.textContent = formatPrice(total);
        });
        document.querySelectorAll('.pax-count-display').forEach(el => {
            el.textContent = passengerCount;
        });
        document.querySelectorAll('.unit-price-display').forEach(el => {
            el.textContent = formatPrice(unitPrice);
        });
    }

    if (els.currencySelector) {
        els.currencySelector.addEventListener('change', (e) => {
            currentCurrency = e.target.value;
            unitPrice = pricingOptions[currentCurrency];
            els.formCurrencyInput.value = currentCurrency;
            updatePrice();
        });
    }

    // --- PASSENGER MANAGEMENT ---
    function createPassengerRow(index) {
        const div = document.createElement('div');
        div.className = "passenger-row bg-gray-50 p-6 rounded-xl border border-gray-200 relative animate-fade-in mb-6 transition-all duration-300 hover:shadow-md";
        div.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <h4 class="font-bold text-gray-700 uppercase tracking-wide text-sm flex items-center gap-2">
                    <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs">
                        <i class="fas fa-user"></i>
                    </span>
                    Voyageur ${index + 1}
                </h4>
                ${index > 0 ? `<button type="button" class="w-12 h-12 rounded-full bg-red-100 text-red-600 hover:bg-red-200 flex items-center justify-center transition-colors remove-pax" title="Supprimer"><i class="fas fa-trash-alt text-lg"></i></button>` : '<span class="text-xs font-bold text-blue-600 bg-blue-50 border border-blue-100 px-3 py-1 rounded-full uppercase tracking-wide">Titulaire</span>'}
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="md:col-span-1">
                    <label class="block text-gray-400 text-xs font-bold mb-2 uppercase tracking-wide">Nom Complet</label>
                    <input class="w-full bg-white text-gray-900 font-bold border-2 border-transparent focus:border-blue-500 focus:bg-white rounded-xl py-3 px-4 transition-colors placeholder-gray-300 bg-gray-100"
                           name="passenger_name[]" type="text" required placeholder="ex: KABILA JOSEPH">
                </div>
                <div class="md:col-span-1">
                     <label class="block text-gray-400 text-xs font-bold mb-2 uppercase tracking-wide">Type Document</label>
                     <div class="relative">
                         <select class="w-full bg-white text-gray-900 font-bold border-2 border-transparent focus:border-blue-500 focus:bg-white rounded-xl py-3 px-4 appearance-none transition-colors bg-gray-100"
                               name="document_type[]" required>
                                <option value="Passeport" selected>Passeport</option>
                                <option value="Carte d'Identité">Carte d'Identité</option>
                                <option value="Permis de Conduire">Permis de Conduire</option>
                                <option value="Carte d'Électeur">Carte d'Électeur</option>
                            </select>
                            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
                                <i class="fas fa-chevron-down text-xs"></i>
                            </div>
                    </div>
                </div>
                <div class="md:col-span-1">
                    <label class="block text-gray-400 text-xs font-bold mb-2 uppercase tracking-wide">Numéro Document</label>
                    <input class="w-full bg-white text-gray-900 font-bold border-2 border-transparent focus:border-blue-500 focus:bg-white rounded-xl py-3 px-4 transition-colors placeholder-gray-300 bg-gray-100"
                           name="passport[]" type="text" required placeholder="ex: A1234567">
                </div>
            </div>
        `;

        if (index > 0) {
            div.querySelector('.remove-pax').addEventListener('click', () => {
                div.remove();
                passengerCount--;
                updateLabels();
                updatePrice();
            });
        }
        return div;
    }

    function updateLabels() {
        const rows = els.passengersContainer.querySelectorAll('.passenger-row');
        let idx = 0;
        rows.forEach((row) => {
            const title = row.querySelector('h4');
            // Preserve the icon inside
            title.innerHTML = `
                <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs">
                    <i class="fas fa-user"></i>
                </span>
                Voyageur ${idx + 1}
            `;
            idx++;
        });
    }

    els.btnAddPassenger.addEventListener('click', () => {
        const newRow = createPassengerRow(passengerCount);
        els.passengersContainer.appendChild(newRow);
        passengerCount++;
        updatePrice();
    });

    // --- STEPPER LOGIC ---
    els.btnContinue.addEventListener('click', () => {
        if (els.form.checkValidity()) {
            // Lock Step 2
            // identitySection.classList.add('opacity-50', 'pointer-events-none');

            // Show Step 3
            els.paymentSection.classList.remove('hidden');

            // Update Stepper UI
            els.step2Indicator.classList.remove('bg-blue-600', 'text-white');
            els.step2Indicator.classList.add('bg-green-500', 'text-white');
            els.step2Indicator.innerHTML = '<i class="fas fa-check"></i>';

            els.step3Indicator.classList.remove('bg-gray-200', 'text-gray-500');
            els.step3Indicator.classList.add('bg-blue-600', 'text-white');

            // Update Mobile Stepper
            if(els.mobileStepNum) {
                els.mobileStepNum.textContent = "3";
                els.mobileStepName.textContent = "Paiement";
                document.getElementById('mobile-progress-bar').style.width = "100%";
            }

            // Toggle Buttons
            els.btnContinue.classList.add('hidden');
            document.getElementById('payment-actions').classList.remove('hidden');
            document.getElementById('add-pax-wrapper').classList.add('hidden'); // Disable adding more pax

            // Scroll
            els.paymentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            els.form.reportValidity();
        }
    });

    // --- STRIPE LOGIC ---
    loadStripe();

    async function loadStripe() {
        try {
            const res = await fetch('/api/settings/public');
            const conf = await res.json();

            if (conf.stripe_enabled) {
                stripeEnabled = true;
                document.getElementById('option-stripe').classList.remove('hidden');
                stripe = Stripe('pk_test_TYooMQauvdEDq54NiTphI7jx'); // Demo Key
                elements = stripe.elements();
                card = elements.create('card', {
                    style: {
                        base: {
                            color: '#32325d',
                            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
                            fontSmoothing: 'antialiased',
                            fontSize: '16px',
                            '::placeholder': {
                                color: '#aab7c4'
                            }
                        },
                        invalid: {
                            color: '#fa755a',
                            iconColor: '#fa755a'
                        }
                    }
                });
                card.mount('#card-element');
            }
        } catch (e) {
            console.error("Error loading settings", e);
        }
    }

    // Toggle Stripe & Mobile Money Inputs
    const radios = document.querySelectorAll('input[name="payment_method"]');
    const stripeSection = document.getElementById('stripe-section');
    const mobileMoneySection = document.getElementById('mobile-money-section');

    radios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'STRIPE') {
                stripeSection.classList.remove('hidden');
                if(mobileMoneySection) mobileMoneySection.classList.add('hidden');
            } else if (e.target.value === 'MOBILE_MONEY') {
                stripeSection.classList.add('hidden');
                if(mobileMoneySection) mobileMoneySection.classList.remove('hidden');
            } else {
                stripeSection.classList.add('hidden');
                if(mobileMoneySection) mobileMoneySection.classList.add('hidden');
            }
        });
    });

    // Form Submit
    els.form.addEventListener('submit', async (e) => {
        const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;

        if (isDemoMode) {
             // In Demo Mode, just show spinner and submit
             setLoading(true);
             // Allow form submission to proceed
             return;
        }

        if (paymentMethod === 'STRIPE' && stripeEnabled) {
            e.preventDefault();
            setLoading(true);

            try {
                const intentRes = await fetch('/api/payment/create-intent', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': checkoutConfig.csrfToken
                    },
                    body: JSON.stringify({
                        flight_id: checkoutConfig.flightId,
                        passenger_name: "Multi-Pax Group", // Placeholder for intent desc
                        quantity: passengerCount
                    })
                });

                const intentData = await intentRes.json();
                if (intentData.error) throw new Error(intentData.error);

                const result = await stripe.confirmCardPayment(intentData.clientSecret, {
                    payment_method: {
                        card: card,
                        billing_details: { name: "GoPass Customer" }
                    }
                });

                if (result.error) {
                    document.getElementById('card-errors').textContent = result.error.message;
                    setLoading(false);
                } else {
                    if (result.paymentIntent.status === 'succeeded') {
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.name = 'stripe_payment_intent';
                        hiddenInput.value = result.paymentIntent.id;
                        els.form.appendChild(hiddenInput);

                        els.form.submit();
                    }
                }
            } catch (err) {
                document.getElementById('card-errors').textContent = err.message;
                setLoading(false);
            }
        }
    });

    function setLoading(isLoading) {
        const btn = document.querySelector('#btn-pay');
        if (isLoading) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Traitement...';
        } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-lock mr-2"></i> Payer & Générer Billets';
        }
    }

    // Initialize
    updatePrice();
}
