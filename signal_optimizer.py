# Continuing from where we left off...
        # Plot patterns by hour and day
        plt.subplot(2, 2, 2)
        plt.scatter(self.data['hour'], self.data['day_of_week'], c=self.data['pattern'], cmap='viridis', s=50)
        plt.title('Traffic Patterns by Hour and Day')
        plt.xlabel('Hour of Day')
        plt.ylabel('Day of Week (0=Monday, 6=Sunday)')
        plt.colorbar(label='Pattern')
        plt.yticks(range(7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        plt.xticks(range(0, 24, 3))
        
        # Plot average vehicle count by hour for each pattern
        plt.subplot(2, 2, 3)
        for pattern in self.data['pattern'].unique():
            pattern_data = self.data[self.data['pattern'] == pattern]
            hourly_avg = pattern_data.groupby('hour')['vehicle_count'].mean()
            plt.plot(hourly_avg.index, hourly_avg.values, label=f'Pattern {pattern}')
        plt.title('Average Vehicle Count by Hour for Each Pattern')
        plt.xlabel('Hour of Day')
        plt.ylabel('Average Vehicle Count')
        plt.legend()
        
        # Plot distribution of patterns
        plt.subplot(2, 2, 4)
        pattern_counts = self.data['pattern_name'].value_counts()
        plt.pie(pattern_counts, labels=pattern_counts.index, autopct='%1.1f%%')
        plt.title('Distribution of Traffic Patterns')
        
        plt.tight_layout()
        plt.savefig('traffic_patterns.png')
        plt.close()

def main():
    optimizer = TrafficSignalOptimizer('traffic_data.csv')
    
    # Identify patterns
    pattern_summary = optimizer.identify_patterns()
    print("Traffic Pattern Summary:")
    print(pattern_summary)
    
    # Build and train prediction model
    history = optimizer.build_prediction_model()
    
    # Visualize patterns
    optimizer.visualize_patterns()
    
    # Generate optimal signal timing for each pattern
    for pattern in ['Light', 'Moderate', 'Heavy', 'Congested']:
        timing = optimizer.optimize_signal_timing(pattern)
        print(f"\nOptimal Signal Timing for {pattern} Traffic:")
        for key, value in timing.items():
            print(f"  {key}: {value} seconds")
    
    # Predict future patterns
    future_predictions = optimizer.predict_future_pattern(24)
    print("\nPredicted Traffic Patterns for Next 24 Hours:")
    print(future_predictions[['hour', 'vehicle_count', 'pattern']])
    
    # Save predictions
    future_predictions.to_csv('predicted_traffic_patterns.csv', index=False)

if __name__ == "__main__":
    main()