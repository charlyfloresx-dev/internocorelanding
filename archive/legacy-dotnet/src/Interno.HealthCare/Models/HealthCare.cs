using System.ComponentModel.DataAnnotations;

namespace Interno.HealthCare.Models
{
    public class HealthCare 
    {
        [KeyAttribute]
        public int Id { get; set; }
        [RequiredAttribute]
        public Care Care { get; set; } // Cuidado del Listado Registrado
        [RequiredAttribute]
        public float Value { get; set; } // Cantidad o Valor
        public string Observations { get; set; } 
        public Interno.HealthCare.Models.HospitalUser Specialist { get; set; }   
    }
}