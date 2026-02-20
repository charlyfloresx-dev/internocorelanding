using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Interno.Domain.Catalog;

namespace Interno.Gym
{
    public class Partner 
    {
        public int PersonId { get; set; }
        public Interno.Domain.Catalog.Person Person { get; set; }
        [NotMapped]
        public ICollection<Subscription>? Subscriptions { get; set; }
    }
}