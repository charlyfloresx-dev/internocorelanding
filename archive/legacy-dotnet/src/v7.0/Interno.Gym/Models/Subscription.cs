using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Gym
{
    public class Subscription
    {
        [Key]
        public Guid Id { get; set; }
        [Required]
        public int PartnerId { get; set; }

        public Partner Partner { get; set; }
        [Required]
        public SubscriptionType Type { get; set; }
        [Required]
        public DateTime Start { get; set; }
        public DateTime End { get; set; } // this.Start.AddTicks(Subscription.getTicks((SubscriptionType)data.Type)).AddDays(1).Date;
        public bool Coupon { get; set; }
        public string? CouponNumber { get; set; }
        public virtual bool Active { get { return (this.End < DateTime.Now.Date) ? false : true; } }
        //Data Info
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;
        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;

        public static long getTicks(SubscriptionType type)
        {
            switch (type)
            {
                case SubscriptionType.Day: return DateTime.MinValue.AddDays(1).Ticks;
                case SubscriptionType.Week: return DateTime.MinValue.AddDays(7).Ticks;
                case SubscriptionType.Month: return DateTime.MinValue.AddMonths(1).Ticks;
                case SubscriptionType.Quarter: return DateTime.MinValue.AddMonths(3).Ticks;
                case SubscriptionType.Semester: return DateTime.MinValue.AddMonths(6).Ticks;
                case SubscriptionType.Year: return DateTime.MinValue.AddMonths(12).Ticks;
                default: return 0;
            }
        }
        public Subscription()
        {
            this.Start = DateTime.Now;
            //this.Active = true;
        }
    }

    public enum SubscriptionType
    {
        Day,
        Week,
        Month,
        Quarter,
        Semester,
        Year
    }
}