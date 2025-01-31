/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ["class"],
	content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
	theme: {
		fontSize: {
			"xsm": '11px',
			sm: '13px',
			base: '15px',
			xl: '17px',
			'2xl': '21px',
			// '3xl': '1.953rem',
			// '4xl': '2.441rem',
			// '5xl': '3.052rem',
		},
		fontWeight: {
			thin: '100',
			extralight: '200',
			light: '300',
			normal: '400',
			medium: '500',
			semibold: '600',
			bold: '700',
			extrabold: '800',
			black: '900',
		},
		extend: {
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 6px)'
			},
			colors: {
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))',
					secondary: 'hsl(var(--popover-secondary))'
				},
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))',
					success: 'hsla(var(--success))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				disabled: {
					foreground: 'hsl(var(--disabled-foreground))',
				},
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))'
				}
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'jump': {
					'0%, 100%': {
						transform: 'translateY(0)',
						animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)',
					},
					'50%': {
						transform: 'translateY(-8px)',
						animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)',
					},
				},
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'jump': 'jump 1s infinite',
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
}
