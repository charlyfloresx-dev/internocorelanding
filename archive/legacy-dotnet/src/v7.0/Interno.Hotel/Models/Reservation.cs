using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Hotel.Models
{
    public class Reservation
    {
        [Key]
        public int Id { get; set; }
        public Room Room { get; set; }
        public ReservationStatus Status { get; set; }
        public DateTime In { get; set; }
        public DateTime Out { get; set; }
        public Interno.Domain.Catalog.Phone Phone { get; set; }
        public Interno.Domain.Catalog.Person Guest { get; set; }
        public string ReservationNumber { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;

        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;

        public Reservation()
        {
            this.Phone = new Interno.Domain.Catalog.Phone();
        }

        private string generateReservationString() => Guid.NewGuid().ToString("n");
    }
}