using System.ComponentModel.DataAnnotations;
using Interno.Domain.Catalog;

namespace Interno.HealthCare.Models
{
    public class Prescription
    {
        [Key]
        public int Id { get; set; }
        public Medicine Medicament { get; set; }
        //FALTA AGREGARLE MUCHO
    }
}